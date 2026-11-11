"""Spreekt ontbrekende teksten in met Azure (Maarten) en zet ze in audio/m2.
Leest stemmen/nieuw.tsv (hash TAB tekst). Bestaat audio/m2/<hash>.mp3 al, dan wordt die overgeslagen."""
import json, os, sys, time, subprocess, urllib.request, urllib.error
from xml.sax.saxutils import escape
KEY=os.environ.get('AZURE_SPEECH_KEY','').strip(); REG=os.environ.get('AZURE_SPEECH_REGION','westeurope').strip().lower()
if not KEY: sys.exit('AZURE_SPEECH_KEY ontbreekt (Settings > Secrets and variables > Actions).')
# korter maken: stilte aan begin en eind weg, lange pauzes tussen zinsdelen ingekort, iets vlotter tempo
KORT='silenceremove=start_periods=1:start_threshold=-48dB:start_silence=0.03:stop_periods=-1:stop_duration=0.12:stop_threshold=-45dB:stop_silence=0.08,atempo=1.05'
def kort(pad):
    tmp=pad+'.tmp.mp3'
    r=subprocess.run(['ffmpeg','-nostdin','-loglevel','error','-y','-i',pad,'-af',KORT,'-ar','24000','-ac','1','-b:a','48k',tmp])
    if r.returncode==0 and os.path.getsize(tmp)>500: os.replace(tmp,pad)
    elif os.path.exists(tmp): os.remove(tmp)
URL=f'https://{REG}.tts.speech.microsoft.com/cognitiveservices/v1'
D='audio/m2'; idxf=os.path.join(D,'index.json'); idx=json.load(open(idxf,encoding='utf-8')); have=set(idx['h'])
rows=[l.rstrip('\r\n').lstrip('﻿').split('\t',1) for l in open('stemmen/nieuw.tsv',encoding='utf-8') if '\t' in l]
todo=[(h,t) for h,t in rows if not os.path.exists(os.path.join(D,h+'.mp3'))]
print(f'{len(rows)} teksten, {len(todo)} nog in te spreken')
for n,(h,t) in enumerate(todo,1):
    say=t.replace(' = ',' is ').replace(' .','.').replace(' ,',',')
    ssml=f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='nl-NL'><voice name='nl-NL-MaartenNeural'><prosody rate='-6%'>{escape(say)}</prosody></voice></speak>"
    for poging in range(8):
        req=urllib.request.Request(URL,data=ssml.encode('utf-8'),method='POST',headers={'Ocp-Apim-Subscription-Key':KEY,'Content-Type':'application/ssml+xml; charset=utf-8','X-Microsoft-OutputFormat':'audio-24khz-48kbitrate-mono-mp3'})
        try:
            data=urllib.request.urlopen(req,timeout=60).read()
            if len(data)<500: raise RuntimeError('te klein')
            open(os.path.join(D,h+'.mp3'),'wb').write(data); kort(os.path.join(D,h+'.mp3')); break
        except urllib.error.HTTPError as e:
            if e.code in (401,403): sys.exit('Sleutel of regio klopt niet.')
            time.sleep(min(60,10*(poging+1)))
        except Exception:
            time.sleep(min(60,10*(poging+1)))
    else: print('overgeslagen:',t)
    if n%20==0: print(n,'/',len(todo),flush=True)
    time.sleep(3.1)   # gratis tegoed: max 20 per minuut
for h,_ in rows:
    if os.path.exists(os.path.join(D,h+'.mp3')): have.add(h)
idx['h']=sorted(have); json.dump(idx,open(idxf,'w',encoding='utf-8'))
print('klaar,',len(have),'fragmenten in index')
