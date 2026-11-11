#!/usr/bin/env python3
"""Regenerate the 100-unit / 750-word data and package this GitHub repository.

Install generator dependencies: python -m pip install -r requirements-generator.txt
Examples:
  python generate_project.py
  python generate_project.py --output generated
  python generate_project.py --validate
  python generate_project.py --zip
"""
from __future__ import annotations
import argparse, csv, shutil, subprocess, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONSONANTS = ["B","CH","D","DH","F","G","HH","JH","K","L","M","N","NG","P","R","S","SH","T","TH","V","W","Y","Z","ZH"]
VOWELS = ["AA","AE","AH","AO","AW","AY","EH","ER","EY","IH","IY","OW","OY","UH","UW"]
DIPHONES = ["B_AE","K_AE","D_AH","M_IY","S_IH","T_AA","R_EH","L_OW","W_AH","F_AO","P_IH","N_IY","G_OW","SH_IY","CH_EH","TH_AE","DH_AH","V_EH","Z_IY","HH_AE","K_IY","B_OW","M_AE","S_AA","T_IY","R_AA","L_IY","N_AE","P_AA","D_IY","W_IY"]
EXAMPLES = {"B":"bat","CH":"chair","D":"dog","DH":"this","F":"fish","G":"go","HH":"hat","JH":"jam","K":"cat","L":"love","M":"man","N":"no","NG":"sing","P":"pen","R":"red","S":"sun","SH":"ship","T":"top","TH":"thin","V":"van","W":"wet","Y":"yes","Z":"zoo","ZH":"measure","AA":"father","AE":"cat","AH":"about","AO":"thought","AW":"out","AY":"my","EH":"bed","ER":"bird","EY":"day","IH":"sit","IY":"see","OW":"go","OY":"boy","UH":"book","UW":"blue"}

def build_data(out: Path) -> None:
    try:
        import cmudict
        from textblob.en import spelling
    except ImportError as exc:
        raise SystemExit("Missing generator dependency. Run: python -m pip install -r requirements-generator.txt") from exc
    units=[]
    for phone in CONSONANTS:
        units.append({"unit_id":f"U{len(units)+1:03d}","phonetic_symbol":phone,"unit_type":"phoneme","description":f"ARPAbet consonant phoneme {phone}","example_word":EXAMPLES[phone],"notes":"Canonical General American English phoneme; CMU ARPAbet."})
    for vowel in VOWELS:
        for stress in "012":
            units.append({"unit_id":f"U{len(units)+1:03d}","phonetic_symbol":vowel+stress,"unit_type":"stressed_vowel","description":f"ARPAbet vowel {vowel}, stress level {stress}","example_word":EXAMPLES[vowel],"notes":"Stress digit follows CMU Pronouncing Dictionary convention."})
    for pair in DIPHONES:
        left,right=pair.split("_")
        units.append({"unit_id":f"U{len(units)+1:03d}","phonetic_symbol":pair,"unit_type":"optional_diphone","description":f"Optional coarticulation unit {left} transitioning into {right}","example_word":"example","notes":"Reserved optional transition unit; not used by canonical dictionary entries."})
    if len(units)!=100: raise RuntimeError(f"Expected 100 sound units, got {len(units)}")
    by_symbol={u["phonetic_symbol"]:u["unit_id"] for u in units}
    pronunciations=cmudict.dict(); candidates=[]
    for word,freq in spelling.items():
        word=word.lower()
        if word.isalpha() and 2<=len(word)<=15 and freq>0 and word in pronunciations:
            candidates.append((word,int(freq)))
    candidates=sorted(set(candidates),key=lambda x:(-x[1],x[0]))[:750]
    if len(candidates)!=750: raise RuntimeError(f"Need 750 words; found {len(candidates)}")
    rows=[]
    for word,_freq in candidates:
        phones=pronunciations[word][0]
        try: ids=[by_symbol[p] for p in phones]
        except KeyError as exc: raise RuntimeError(f"Unmapped phone {exc} in {word}")
        rows.append({"word":word,"arpabet":" ".join(phones),"unit_sequence":" ".join(ids)})
    out.mkdir(parents=True,exist_ok=True)
    for filename,data,fields in [("sound_units.csv",units,["unit_id","phonetic_symbol","unit_type","description","example_word","notes"]),("pronunciation_dictionary.csv",rows,["word","arpabet","unit_sequence"] )]:
        with (out/filename).open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(data)
    # Generate a compact MicroPython lookup module for on-device speech mode.
    packed="\n".join(f"{r['word']}|{r['arpabet']}" for r in rows)
    (out/"onboard_dictionary.py").write_text(
        "# Generated from pronunciation_dictionary.csv by generate_project.py.\n"
        "# Compact packed data: one word|CMU-ARPAbet entry per line.\n"
        "ONBOARD_DICTIONARY = r\"\"\""+packed+"\"\"\"\nWORD_COUNT = 750\n",
        encoding="utf-8")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,help="Output directory; default is this repository")
    parser.add_argument("--validate",action="store_true",help="Run the repository validator")
    parser.add_argument("--zip",action="store_true",help="Create microbit-english-speech-engine.zip")
    args=parser.parse_args()
    out=(args.output.resolve() if args.output else ROOT)
    if out!=ROOT:
        if out.exists(): shutil.rmtree(out)
        shutil.copytree(ROOT,out,ignore=shutil.ignore_patterns(".git","__pycache__","*.zip","generated"))
    build_data(out)
    # Always validate generated output before packaging or reporting success.
    result=subprocess.run([sys.executable,str(out/"validate_dictionary.py")],cwd=out)
    if result.returncode: return result.returncode
    if args.zip:
        target=out/"microbit-english-speech-engine.zip"
        with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED) as z:
            for path in sorted(out.rglob("*")):
                if path.is_file() and path!=target and ".git" not in path.parts and "__pycache__" not in path.parts:
                    z.write(path,Path(out.name)/path.relative_to(out))
        with zipfile.ZipFile(target) as z:
            bad=z.testzip()
            if bad: raise RuntimeError(f"ZIP integrity error: {bad}")
        print(f"Created {target} ({target.stat().st_size:,} bytes)")
    return 0
if __name__=="__main__": raise SystemExit(main())
