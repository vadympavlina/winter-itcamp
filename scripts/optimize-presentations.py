#!/usr/bin/env python3
"""Оптимізація продуктивності презентацій lessons/*/presentation-*.html.

Нічого не змінює в картинках, шрифтах і текстах. Прибирає/здешевлює те, що вантажить процесор і відеокарту:
  * важкі CSS-ефекти (blur на весь екран, backdrop-filter, анімація filter/inset);
  * перемальовування canvas на 60 кадрів/с, коли нічого не рухається (тоді ~30 або ~12 кадрів/с);
  * надто висока щільність пікселів canvas/WebGL (2 -> 1.5);
  * blur у GSAP-переходах слайдів;
  * для 3D-сцени: менша карта тіней і 30 кадрів/с у спокої.
Скрипт ідемпотентний: у файлі лишається маркер <!--perf-optimized-->. Запуск:  python3 scripts/optimize-presentations.py
"""
import re, sys
from pathlib import Path

MARK = "<!--perf-optimized-->"
root = Path(__file__).resolve().parent.parent


def sub(s, old, new, name, count=1, regex=False):
    n = len(re.findall(old, s)) if regex else s.count(old)
    if n != count:
        raise SystemExit(f"  !! {name}: очікував {count} збіг(ів), знайдено {n}")
    return re.sub(old, new, s) if regex else s.replace(old, new)


def common(s):
    # щільність пікселів canvas / WebGL: 2 -> 1.5 (на ретина-екранах це на 44% менше пікселів)
    n = s.count("Math.min(devicePixelRatio,2)")
    if not n:
        raise SystemExit("  !! DPR не знайдено")
    return s.replace("Math.min(devicePixelRatio,2)", "Math.min(devicePixelRatio,1.5)")


def family_6_8(s):
    # 1. аврора: blur(60px) на півекрана + mix-blend-mode, що анімуються -> м'які градієнти без фільтра
    s = sub(s, "pointer-events:none;filter:blur(60px);opacity:.55}", "pointer-events:none;opacity:.55}", "aurora blur")
    s = sub(s, "border-radius:50%;mix-blend-mode:screen;animation:drift", "border-radius:50%;animation:drift", "aurora blend")
    s, n = re.subn(r"(\.aurora i:nth-child\(\d\)\{[^}]*?)background:(#[0-9a-f]{6})([0-9a-f]{2})(?=[;}])",
            r"\1background:radial-gradient(closest-side,\2\3 55%,\g<2>00)", s)
    if n < 2:
        raise SystemExit(f"  !! aurora gradients: знайдено {n}")
    # 2. гірлянда: анімація filter:drop-shadow -> лише opacity + статичне гало
    s = sub(s, "@keyframes blink{0%,100%{opacity:1;filter:drop-shadow(0 0 6px currentColor)}50%{opacity:.35;filter:none}}",
            "@keyframes blink{0%,100%{opacity:1}50%{opacity:.35}}", "bulb keyframes")
    s = sub(s, '<ellipse cx="${x}" cy="${y+14}" rx="7" ry="11" fill="${c}"/></g>',
            '<ellipse cx="${x}" cy="${y+14}" rx="12" ry="17" fill="${c}" opacity=".25"/><ellipse cx="${x}" cy="${y+14}" rx="7" ry="11" fill="${c}"/></g>', "bulb halo")
    # 3. blur у GSAP-переходах слайдів (opacity/scale/y лишаються)
    for b in ("blur(8px)", "blur(0px)", "blur(10px)"):
        s = sub(s, f",filter:'{b}'", "", "gsap " + b)
    # 4. ліс на canvas: повна перемальовка лише коли рухається камера/миша, у спокої ~12 к/с (мерехтіння зірок і вікон лишається)
    s = sub(s, "function resize(){DPR=", "function resize(){_bt=-1;DPR=", "resize")
    s = sub(s, "function loop(){",
            "var _bk=[1e9,0,0],_bt=-1,_sa=0,_sn=0;\n"
            "function bgStep(t){const m=Math.abs(cam.x-_bk[0])>.15||Math.abs(mouse.sx-_bk[1])>.003||Math.abs(mouse.sy-_bk[2])>.003;\n"
            "  if(m||_bt<0||t-_bt>.08){_bk=[cam.x,mouse.sx,mouse.sy];_bt=t;drawBg(t)}}\n"
            "function loop(){", "loop head")
    s = sub(s, "drawBg(t);drawSnow(sbCtx,back,dt,t,2.2,.35,1.6);drawSnow(sfCtx,front,dt,t,1.3,.2,.4);",
            "bgStep(t);_sa+=dt;if(snow.rush>.01||(_sn++&1)){drawSnow(sbCtx,back,_sa,t,2.2,.35,1.6);drawSnow(sfCtx,front,_sa,t,1.3,.2,.4);_sa=0}", "loop draw")
    # 5. backdrop-filter над анімованим canvas (є лише в частині файлів) -> трохи щільніший фон без розмиття
    if "backdrop-filter:blur(" in s:
        s = re.sub(r"backdrop-filter:blur\(\d+px\);-webkit-backdrop-filter:blur\(\d+px\);?", "", s)
        s = s.replace("rgba(18,58,138,.72),rgba(6,26,69,.72)", "rgba(18,58,138,.9),rgba(6,26,69,.9)")
        s = s.replace(".plan{background:rgba(6,26,69,.72)", ".plan{background:rgba(6,26,69,.9)")
        s = s.replace("z-index:40;display:flex;align-items:center;gap:14px;background:rgba(6,26,69,.7)", "z-index:40;display:flex;align-items:center;gap:14px;background:rgba(6,26,69,.9)")
    return s


ARENA_THROTTLE = (
    "var _aa=0,_an=0,_ap=-9,_am=-9;\n"
    "function drawArena(t,dt){_aa+=dt;const mv=Math.abs(%(cam)s.pan-_ap)>.01||Math.abs(mouse.sx-_am)>.002;\n"
    "  if(!mv&&%(cam)s.speed<.1&&(_an++&1))return;_ap=%(cam)s.pan;_am=mouse.sx;const d=_aa;_aa=0;drawArenaFull(t,d)}\n"
)
FX_SKIP = ("function drawFx(dt){if(!conf.length){if(window.__fxd){fctx.setTransform(DPR,0,0,DPR,0,0);fctx.clearRect(0,0,W,H);window.__fxd=false}return}"
           "window.__fxd=true;fctx.setTransform(DPR,0,0,DPR,0,0);")


def family_9_14(s, cam, three=False):
    # арена на canvas (режим 'lighter', повноекранні градієнти): у спокої 30 к/с, під час руху - повна частота
    s = sub(s, "function drawArena(t,dt){", "function drawArenaFull(t,dt){", "arena rename")
    s = sub(s, "/* confetti */" if "/* confetti */" in s else "const fx=$('#fx')",
            (ARENA_THROTTLE % {"cam": cam}) + ("/* confetti */" if "/* confetti */" in s else "const fx=$('#fx')"), "arena wrapper")
    # конфеті: не чистимо/не малюємо повноекранний canvas, поки нема конфеті
    s = sub(s, "function drawFx(dt){fctx.setTransform(DPR,0,0,DPR,0,0);", FX_SKIP, "fx skip")
    # нескінченна анімація inset (змушує браузер перераховувати layout щокадру) -> transform
    if "@keyframes ring{to{inset:-20px;opacity:0}}" in s:
        s = s.replace("@keyframes ring{to{inset:-20px;opacity:0}}", "@keyframes ring{to{transform:scale(1.3);opacity:0}}")
    if three:
        s = sub(s, "{antialias:true,alpha:false,preserveDrawingBuffer:true}", "{antialias:true,alpha:false,powerPreference:'high-performance'}", "renderer opts")
        s = sub(s, "d.shadow.mapSize.set(2048,2048)", "d.shadow.mapSize.set(1024,1024)", "shadow map")
        s = sub(s, "function loop(){", "var _r3=0;\nfunction loop(){", "loop head 3d")
        # у спокої (автообертання) 3D-сцена малюється 30 к/с; під час взаємодії - 60
        s = sub(s, "renderExhibit()}\n", "if(!(E.every(o=>now()-o.idle>2.5)&&(_r3++&1)))renderExhibit()}\n", "exhibit render")
        s = sub(s, "renderer.render(sc,o.cam)}}}", "if(!(now()-o.idle>3.5&&!gsap.isTweening(o)&&(_r3++&1)))renderer.render(sc,o.cam)}}}", "scene render")
    return s


def process(path):
    s = path.read_text(encoding="utf-8")
    if MARK in s:
        print(f"= {path.name}: вже оптимізовано"); return
    name = path.name
    if "-6-8-" in name:
        s = family_6_8(s)
    elif name.endswith("9-14-day-3.html"):
        s = family_9_14(s, "cam2", three=True)
    else:
        s = family_9_14(s, "cam")
    s = common(s)
    s = s.replace("<head>", "<head>" + MARK, 1) if "<head>" in s else MARK + s
    path.write_text(s, encoding="utf-8")
    print(f"+ {path.name}: оптимізовано")


if __name__ == "__main__":
    files = sorted((root / "lessons").glob("*/presentation-*.html"))
    if not files:
        sys.exit("Презентацій не знайдено")
    for f in files:
        try:
            process(f)
        except SystemExit as e:
            print(f"x {f.name}: {e}")
