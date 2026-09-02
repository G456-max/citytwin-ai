import os
import sys
import math
import wave
import subprocess
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import win32com.client
import imageio_ffmpeg

WIDTH = 1920
HEIGHT = 1080
FPS = 30
TEMP_VIDEO = "temp_render_video.mp4"
TEMP_AUDIO = "temp_master_audio.wav"
FINAL_OUTPUT = "citytwin_ai_final_presentation.mp4"

# Colors
BG_DARK = (9, 13, 22)
BG_CARD = (17, 24, 39)
BORDER_COLOR = (30, 41, 59)
CYAN = (56, 189, 248)
EMERALD = (52, 211, 153)
ROSE = (244, 63, 94)
GOLD = (251, 191, 36)
PURPLE = (168, 85, 247)
WHITE = (255, 255, 255)
GRAY = (148, 163, 184)
LIGHT_GRAY = (226, 232, 240)

FONT_DIR = Path("C:/Windows/Fonts")
font_hero = ImageFont.truetype(str(FONT_DIR / "segoeuib.ttf"), 72)
font_title = ImageFont.truetype(str(FONT_DIR / "segoeuib.ttf"), 44)
font_subtitle = ImageFont.truetype(str(FONT_DIR / "segoeui.ttf"), 24)
font_card_title = ImageFont.truetype(str(FONT_DIR / "segoeuib.ttf"), 24)
font_body = ImageFont.truetype(str(FONT_DIR / "segoeui.ttf"), 19)
font_mono = ImageFont.truetype(str(FONT_DIR / "consolab.ttf"), 20)
font_mono_small = ImageFont.truetype(str(FONT_DIR / "consolab.ttf"), 15)
font_caption = ImageFont.truetype(str(FONT_DIR / "segoeuib.ttf"), 22)
font_stat_val = ImageFont.truetype(str(FONT_DIR / "segoeuib.ttf"), 38)

def clamp(val, low=0.0, high=1.0):
    return max(low, min(high, val))

def lerp(a, b, t):
    return a + (b - a) * t

def ease_in_out(t):
    return t * t * (3 - 2 * t)

def ease_out_back(t, s=1.4):
    t -= 1
    return t * t * ((s + 1) * t + s) + 1

def draw_header(draw, title_text, step_text="CITYTWIN AI • MUNICIPAL VERIFICATION ENGINE"):
    draw.text((80, 35), step_text, font=font_mono_small, fill=CYAN)
    draw.text((80, 65), title_text, font=font_title, fill=WHITE)
    draw.line([(80, 130), (1840, 130)], fill=BORDER_COLOR, width=2)

def draw_caption_bar(draw, caption_text):
    # Caption bar at bottom of screen
    draw_rounded_rect(draw, (80, 990, 1840, 1045), radius=10, fill=(13, 18, 30), outline=BORDER_COLOR, width=1)
    draw.text((WIDTH // 2, 1017), caption_text, font=font_caption, fill=CYAN, anchor="mm")

def draw_bg_grid(draw, frame_idx):
    for x in range(40, WIDTH, 60):
        for y in range(40, HEIGHT, 60):
            draw.point((x, y), fill=(22, 30, 46))
    scan_y = int((frame_idx * 3) % HEIGHT)
    draw.line([(0, scan_y), (WIDTH, scan_y)], fill=(18, 28, 48), width=1)

def draw_rounded_rect(draw, bbox, radius, fill=None, outline=None, width=1):
    x1, y1, x2, y2 = bbox
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    draw.pieslice([x1, y1, x1 + radius * 2, y1 + radius * 2], 180, 270, fill=fill)
    draw.pieslice([x2 - radius * 2, y1, x2, y1 + radius * 2], 270, 360, fill=fill)
    draw.pieslice([x1, y2 - radius * 2, x1 + radius * 2, y2], 90, 180, fill=fill)
    draw.pieslice([x2 - radius * 2, y2 - radius * 2, x2, y2], 0, 90, fill=fill)
    if outline:
        draw.rounded_rectangle(bbox, radius=radius, outline=outline, width=width)

# Scene Renderers
def render_scene_1(frame_idx, progress):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)
    draw_bg_grid(draw, frame_idx)

    cx, cy = WIDTH // 2, HEIGHT // 2 - 50
    for r_offset in [0, 80, 160, 240, 320]:
        radius = int((frame_idx * 2 + r_offset) % 450)
        alpha = int(255 * (1.0 - radius / 450.0))
        c_val = int(56 * (alpha / 255.0))
        draw.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)], outline=(c_val // 2, c_val, int(248 * (alpha / 255.0))), width=1)

    box_w, box_h = 1100, 480
    bx1 = cx - box_w // 2
    by1 = cy - box_h // 2
    draw_rounded_rect(draw, (bx1, by1, bx1 + box_w, by1 + box_h), radius=20, fill=(13, 18, 30), outline=CYAN, width=2)

    draw_rounded_rect(draw, (cx - 240, by1 + 35, cx + 240, by1 + 72), radius=8, fill=(15, 23, 42), outline=(30, 58, 138), width=1)
    draw.text((cx, by1 + 53), "RAJAHMUNDRY NH-16 CORRIDOR EXPANSION", font=font_mono_small, fill=CYAN, anchor="mm")

    draw.text((cx, cy - 40), "CITYTWIN AI", font=font_hero, fill=WHITE, anchor="mm")
    draw.text((cx, cy + 30), "Dual-Core Municipal Highway Compliance & Generative Verification", font=font_subtitle, fill=LIGHT_GRAY, anchor="mm")

    badges = [
        ("0% Math Hallucination", EMERALD),
        ("Blueprint-Locked Diffusion", CYAN),
        ("Automated Canopy Audit", GOLD),
        ("Instant Municipal PDF Reports", PURPLE)
    ]
    badge_x = cx - 440
    badge_y = cy + 110
    for text, color in badges:
        draw_rounded_rect(draw, (badge_x, badge_y, badge_x + 210, badge_y + 45), radius=8, fill=(17, 24, 39), outline=color, width=1)
        draw.text((badge_x + 105, badge_y + 22), text, font=font_mono_small, fill=WHITE, anchor="mm")
        badge_x += 225

    draw_caption_bar(draw, "CASE STUDY: Rajamahendravaram Godavari Corridor [16.985°N, 81.782°E • UTM Zone 44N]")
    return np.array(img)

def render_scene_2(frame_idx, progress):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)
    draw_bg_grid(draw, frame_idx)
    draw_header(draw, "THE MUNICIPAL ROAD WIDENING BOTTLENECK", "PROBLEM ANALYSIS • RAJAMAHENDRAVARAM CORRIDOR")

    cards = [
        ("01", "Unauthorized Encroachments", "Commercial shops & boundary walls blocking the statutory highway corridor. Manual chainage surveys take weeks.", ROSE),
        ("02", "CAD vs. GPS Datum Shifts", "CAD blueprints in local coordinates fail to align with real-world satellite WGS84 GPS benchmarks.", GOLD),
        ("03", "Undocumented Tree Removal", "Environmental forestry clearances stall projects for months due to slow, manual tree counting.", EMERALD),
        ("04", "Abstract CAD Wireframes", "2D CAD drawings confuse non-technical leaders, while standard AI hallucinates fake, unbuildable roads.", CYAN)
    ]

    for idx, (num, title, desc, col) in enumerate(cards):
        card_t = clamp((progress - idx * 0.12) * 3)
        if card_t <= 0:
            continue
        eased_t = ease_in_out(card_t)
        card_x = 80 + idx * 445
        target_y = 160
        start_y = 280
        card_y = int(lerp(start_y, target_y, eased_t))

        draw_rounded_rect(draw, (card_x, card_y, card_x + 420, card_y + 780), radius=16, fill=BG_CARD, outline=col, width=2)
        draw_rounded_rect(draw, (card_x + 25, card_y + 25, card_x + 75, card_y + 75), radius=10, fill=(15, 23, 42), outline=col, width=1)
        draw.text((card_x + 50, card_y + 50), num, font=font_card_title, fill=col, anchor="mm")
        draw.rectangle([card_x + 25, card_y + 95, card_x + 395, card_y + 97], fill=BORDER_COLOR)
        draw.text((card_x + 25, card_y + 115), title, font=font_card_title, fill=WHITE)
        
        words = desc.split()
        lines = []
        cur = []
        for w in words:
            cur.append(w)
            if len(" ".join(cur)) > 26:
                lines.append(" ".join(cur[:-1]))
                cur = [w]
        if cur:
            lines.append(" ".join(cur))
            
        for l_idx, line in enumerate(lines):
            draw.text((card_x + 25, card_y + 175 + l_idx * 30), line, font=font_body, fill=GRAY)

    draw_caption_bar(draw, "TRADITIONAL BOTTLENECKS: Physical surveys spark boundary disputes & environmental delays")
    return np.array(img)

def render_scene_3(frame_idx, progress):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)
    draw_bg_grid(draw, frame_idx)
    draw_header(draw, "DUAL-ENGINE ARCHITECTURE & 3-POINT GCP SNAPPING", "CORE FOUNDATION • DETERMINISTIC GIS ALIGNMENT")

    lx = 80
    ly = 160
    draw_rounded_rect(draw, (lx, ly, lx + 840, ly + 780), radius=20, fill=BG_CARD, outline=CYAN, width=2)
    draw_rounded_rect(draw, (lx + 35, ly + 30, lx + 380, ly + 70), radius=8, fill=(15, 23, 42), outline=CYAN, width=1)
    draw.text((lx + 45, ly + 50), "ENGINE 1: DETERMINISTIC MATH", font=font_mono_small, fill=CYAN, anchor="lm")
    draw.text((lx + 35, ly + 95), "Metric UTM Spatial Compliance", font=font_card_title, fill=WHITE)
    draw.text((lx + 35, ly + 140), "• 3-Point GCP Affine Snapping Matrix Solver", font=font_body, fill=LIGHT_GRAY)
    draw.text((lx + 35, ly + 175), "• Reprojection to Local UTM Zone 44N (EPSG:32644)", font=font_body, fill=LIGHT_GRAY)
    draw.text((lx + 35, ly + 210), "• Exact Polygon Intersection: Im = Sm ∩ Rm", font=font_body, fill=LIGHT_GRAY)
    draw.text((lx + 35, ly + 245), "• Maximum Intrusion Penetration Depth (D_max)", font=font_body, fill=LIGHT_GRAY)
    draw.text((lx + 35, ly + 280), "• HSV Green Canopy Indexing: 35 <= H <= 85", font=font_body, fill=LIGHT_GRAY)

    draw_rounded_rect(draw, (lx + 35, ly + 340, lx + 805, ly + 720), radius=12, fill=(10, 15, 26), outline=BORDER_COLOR, width=1)
    draw.text((lx + 60, ly + 380), "MATHEMATICAL FORMULATION:", font=font_mono_small, fill=GOLD)
    draw.text((lx + 60, ly + 430), "T = [[a, b, c], [d, e, f], [0, 0, 1]]", font=font_mono, fill=CYAN)
    draw.text((lx + 60, ly + 490), "Area (m2) = DoubleIntegral_{Im} dx dy", font=font_mono, fill=CYAN)
    draw.text((lx + 60, ly + 550), "D_max = max_{pj in Im} dist(pj, Bound_Rm)", font=font_mono, fill=CYAN)
    draw.text((lx + 60, ly + 610), "Vegetation Mask = HSV[35..85, 20..255, 20..255]", font=font_mono, fill=EMERALD)

    rx = 980
    ry = 160
    draw_rounded_rect(draw, (rx, ry, rx + 840, ry + 780), radius=20, fill=BG_CARD, outline=PURPLE, width=2)
    draw_rounded_rect(draw, (rx + 35, ry + 30, rx + 400, ry + 70), radius=8, fill=(15, 23, 42), outline=PURPLE, width=1)
    draw.text((rx + 45, ry + 50), "ENGINE 2: BLUEPRINT-LOCKED DIFFUSION", font=font_mono_small, fill=PURPLE, anchor="lm")
    draw.text((rx + 35, ry + 95), "Geometry-Constrained Visual Twin", font=font_card_title, fill=WHITE)
    draw.text((rx + 35, ry + 140), "• Stable Diffusion + ControlNet Depth Condition Cages", font=font_body, fill=LIGHT_GRAY)
    draw.text((rx + 35, ry + 175), "• Normalizes Photogrammetric DEM Elevation Buffers", font=font_body, fill=LIGHT_GRAY)
    draw.text((rx + 35, ry + 210), "• Zero Hallucination: Preserves Exact Engineering Widths", font=font_body, fill=LIGHT_GRAY)
    draw.text((rx + 35, ry + 245), "• Multi-Weather Synthesizer (Daylight, Night, Monsoon)", font=font_body, fill=LIGHT_GRAY)
    draw.text((rx + 35, ry + 280), "• Deterministic Procedural OpenCV Fallback Engine", font=font_body, fill=LIGHT_GRAY)

    draw_rounded_rect(draw, (rx + 35, ry + 340, rx + 805, ry + 720), radius=12, fill=(10, 15, 26), outline=BORDER_COLOR, width=1)
    draw.text((rx + 60, ry + 380), "ENVIRONMENTAL SCENARIO PRESETS:", font=font_mono_small, fill=GOLD)
    presets = [
        ("Realistic Daylight", "4-lane asphalt, crisp white markings, curbs, trees"),
        ("Nighttime Illumination", "Streetlights glow, headlights, night contrast"),
        ("Monsoon Weather", "Wet asphalt reflections, overcast sky, water runoffs"),
        ("Eco-Green Corridor", "Vertical gardens, green median barriers, potted plants")
    ]
    for p_idx, (p_title, p_sub) in enumerate(presets):
        draw.text((rx + 60, ry + 430 + p_idx * 52), p_title, font=font_mono_small, fill=PURPLE)
        draw.text((rx + 320, ry + 430 + p_idx * 52), p_sub, font=font_body, fill=GRAY)

    draw_caption_bar(draw, "INNOVATION: 3-Point GCP Affine Solver snaps CAD models to real-world GPS coordinates")
    return np.array(img)

def render_scene_4(frame_idx, progress):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)
    draw_bg_grid(draw, frame_idx)
    draw_header(draw, "STEP 1: AUTONOMOUS GIS COMPLIANCE AUDITING", "LIVE DASHBOARD • SPATIAL DISCREPANCY DETECTION")

    # Left Sidebar
    draw_rounded_rect(draw, (80, 150, 420, 960), radius=16, fill=BG_CARD, outline=BORDER_COLOR, width=1)
    draw.text((105, 175), "AUDIT TRIAGE LOGS", font=font_mono_small, fill=CYAN)
    
    triage = [
        ("V-01: Commercial Wall", "Area: 84.20 m² | Depth: 6.2m", "CRITICAL", ROSE),
        ("V-02: Boundary Fence", "Area: 18.50 m² | Depth: 1.8m", "MEDIUM", GOLD),
        ("V-03: Concrete Porch", "Area: 12.00 m² | Depth: 0.9m", "LOW", CYAN),
        ("T-01: Tree Canopy Group", "Clearance: 14 Trees | 320 m²", "FORESTRY", EMERALD)
    ]
    for idx, (t_title, t_desc, t_sev, t_col) in enumerate(triage):
        ty = 210 + idx * 175
        draw_rounded_rect(draw, (100, ty, 400, ty + 155), radius=12, fill=(11, 15, 25), outline=BORDER_COLOR, width=1)
        draw.text((115, ty + 18), t_title, font=font_card_title, fill=WHITE)
        draw.text((115, ty + 55), t_desc, font=font_body, fill=GRAY)
        draw_rounded_rect(draw, (115, ty + 105, 230, ty + 138), radius=6, fill=(15, 23, 42), outline=t_col, width=1)
        draw.text((172, ty + 121), t_sev, font=font_mono_small, fill=t_col, anchor="mm")

    # Center Map Viewport
    mx, my, mw, mh = 460, 150, 1380, 810
    draw_rounded_rect(draw, (mx, my, mx + mw, my + mh), radius=16, fill=(15, 20, 32), outline=BORDER_COLOR, width=1)

    draw.rectangle([mx, my, mx + mw, my + 55], fill=(10, 14, 22))
    draw.line([(mx, my + 55), (mx + mw, my + 55)], fill=BORDER_COLOR, width=1)
    
    stats = [
        ("COMPLIANCE GRADE", "A", EMERALD),
        ("TOTAL VIOLATIONS", "3 Detected", ROSE),
        ("ENCROACHMENT AREA", "114.70 m²", ROSE),
        ("CANOPY CLEARANCE", "320 m² (14 Trees)", EMERALD)
    ]
    for s_idx, (label, val, col) in enumerate(stats):
        sx = mx + 30 + s_idx * 330
        draw.text((sx, my + 18), label + ":", font=font_mono_small, fill=GRAY)
        draw.text((sx + 170, my + 18), val, font=font_mono_small, fill=col)

    # Road Corridor
    road_poly = [(mx + 200, my + mh - 50), (mx + 450, my + 90), (mx + 850, my + 90), (mx + 600, my + mh - 50)]
    draw.polygon(road_poly, fill=(28, 38, 58))
    draw.line([road_poly[0], road_poly[1]], fill=CYAN, width=3)
    draw.line([road_poly[3], road_poly[2]], fill=CYAN, width=3)
    draw.text((mx + 300, my + mh - 100), "SANCTIONED RIGHT-OF-WAY (12m WIDE)", font=font_mono_small, fill=CYAN)

    # Buildings
    draw.polygon([(mx + 100, my + 300), (mx + 250, my + 300), (mx + 250, my + 450), (mx + 100, my + 450)], fill=(40, 50, 70), outline=GRAY)
    
    bldg_viol = [(mx + 380, my + 250), (mx + 560, my + 250), (mx + 560, my + 420), (mx + 380, my + 420)]
    draw.polygon(bldg_viol, fill=(45, 30, 40), outline=GRAY)
    
    pulse = (math.sin(frame_idx * 0.2) + 1.0) / 2.0
    encroach_poly = [(mx + 420, my + 250), (mx + 560, my + 250), (mx + 560, my + 420), (mx + 470, my + 420)]
    encroach_fill = (int(180 + 75 * pulse), int(20 + 20 * pulse), int(50 + 20 * pulse))
    draw.polygon(encroach_poly, fill=encroach_fill, outline=ROSE, width=2)

    callout_x, callout_y = mx + 620, my + 280
    draw.line([(mx + 520, my + 320), (callout_x, callout_y + 40)], fill=ROSE, width=2)
    draw_rounded_rect(draw, (callout_x, callout_y, callout_x + 360, callout_y + 110), radius=10, fill=(10, 15, 25), outline=ROSE, width=2)
    draw.text((callout_x + 20, callout_y + 20), "ENCROACHMENT DETECTED", font=font_mono_small, fill=ROSE)
    draw.text((callout_x + 20, callout_y + 50), "• Overlap Area: 84.20 m²", font=font_body, fill=WHITE)
    draw.text((callout_x + 20, callout_y + 75), "• Max Intrusion: 6.2 meters", font=font_body, fill=GOLD)

    draw.ellipse([(mx + 700, my + 500), (mx + 860, my + 660)], fill=(20, 60, 40), outline=EMERALD, width=2)
    draw.text((mx + 780, my + 580), "CANOPY LOSS\n320 m²", font=font_mono_small, fill=EMERALD, anchor="mm")

    draw_caption_bar(draw, "STEP 1: Deterministic UTM polygon intersection math & HSV green canopy loss calculations")
    return np.array(img)

def render_scene_5(frame_idx, progress):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)
    draw_bg_grid(draw, frame_idx)
    draw_header(draw, "STEP 2: BLUEPRINT-LOCKED GENERATIVE VISUALIZER", "INTERACTIVE WIPE SLIDER • CONTROLNET CAD DIFFUSION")

    sx, sy, sw, sh = 120, 150, 1680, 810
    draw_rounded_rect(draw, (sx, sy, sx + sw, sy + sh), radius=16, fill=(15, 20, 32), outline=BORDER_COLOR, width=1)

    slider_pct = (math.sin((progress * 3.0) * math.pi) + 1.0) / 2.0 * 0.6 + 0.2
    split_x = int(sx + sw * slider_pct)

    # Left Side: Drone Baseline
    draw.rectangle([sx + 5, sy + 5, split_x, sy + sh - 5], fill=(30, 42, 55))
    draw.text((sx + 50, sy + sh - 80), "BASELINE: RAW DRONE ORTHOMOSAIC", font=font_mono, fill=EMERALD)
    draw.text((sx + 50, sy + sh - 45), "Unpaved verges, irregular boundaries, encroaching structures", font=font_body, fill=GRAY)

    # Right Side: Synthesized Road
    draw.rectangle([split_x, sy + 5, sx + sw - 5, sy + sh - 5], fill=(20, 30, 45))
    draw.text((split_x + 50, sy + sh - 80), "SYNTHESIZED: GEOMETRY-LOCKED ROADWAY", font=font_mono, fill=CYAN)
    draw.text((split_x + 50, sy + sh - 45), "Modern 4-lane asphalt, crisp lane markings, streetlights & curbs", font=font_body, fill=GRAY)

    mid_y = sy + sh // 2 - 30
    draw.polygon([(sx + 5, mid_y + 120), (split_x, mid_y + 120), (split_x, mid_y - 120), (sx + 5, mid_y - 120)], fill=(45, 52, 60))
    draw.polygon([(split_x, mid_y + 120), (sx + sw - 5, mid_y + 120), (sx + sw - 5, mid_y - 120), (split_x, mid_y - 120)], fill=(18, 22, 30))
    for stripe_x in range(split_x + 30, sx + sw - 60, 90):
        draw.line([(stripe_x, mid_y), (stripe_x + 50, mid_y)], fill=WHITE, width=4)
        draw.line([(stripe_x, mid_y - 60), (stripe_x + 50, mid_y - 60)], fill=(240, 240, 240), width=2)
        draw.line([(stripe_x, mid_y + 60), (stripe_x + 50, mid_y + 60)], fill=(240, 240, 240), width=2)

    # Split Divider Handle
    draw.line([(split_x, sy + 5), (split_x, sy + sh - 5)], fill=CYAN, width=3)
    draw.ellipse([(split_x - 24, sy + sh // 2 - 24), (split_x + 24, sy + sh // 2 + 24)], fill=(15, 23, 42), outline=CYAN, width=2)
    draw.text((split_x, sy + sh // 2), "< >", font=font_mono_small, fill=CYAN, anchor="mm")

    draw_rounded_rect(draw, (sx + sw - 580, sy + 25, sx + sw - 30, sy + 75), radius=10, fill=(10, 15, 25), outline=BORDER_COLOR, width=1)
    draw.text((sx + sw - 560, sy + 50), "STYLE PRESET: REALISTIC DAYLIGHT (8K RES)", font=font_mono_small, fill=GOLD, anchor="lm")

    draw_caption_bar(draw, "STEP 2: ControlNet depth diffusion ensures 100% geometric adherence with zero hallucinations")
    return np.array(img)

def render_scene_6(frame_idx, progress):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)
    draw_bg_grid(draw, frame_idx)
    draw_header(draw, "STEP 3: ONE-CLICK MUNICIPAL PDF REPORT", "OFFICIAL STATUTORY COMPLIANCE CERTIFICATION")

    doc_t = clamp(progress * 2)
    doc_y = int(lerp(250, 160, ease_out_back(doc_t)))
    dx1, dx2 = 460, 1460
    dy1, dy2 = doc_y, doc_y + 800

    draw_rounded_rect(draw, (dx1 + 10, dy1 + 10, dx2 + 10, dy2 + 10), radius=16, fill=(5, 8, 14))
    draw_rounded_rect(draw, (dx1, dy1, dx2, dy2), radius=16, fill=(248, 250, 252), outline=(203, 213, 225), width=2)

    draw.text((dx1 + 50, dy1 + 45), "MUNICIPAL HIGHWAY STATUTORY COMPLIANCE REPORT", font=font_card_title, fill=(15, 23, 42))
    draw.text((dx1 + 50, dy1 + 80), "Project: Rajamahendravaram Godavari Corridor Expansion • Ref: MH-2026-AP", font=font_body, fill=(71, 85, 105))
    draw.line([(dx1 + 50, dy1 + 115), (dx2 - 50, dy1 + 115)], fill=(203, 213, 225), width=2)

    draw.rectangle([dx1 + 50, dy1 + 135, dx2 - 50, dy1 + 250], fill=(241, 245, 249))
    draw.text((dx1 + 80, dy1 + 160), "STATUTORY CLEARANCE GRADE:", font=font_mono_small, fill=(71, 85, 105))
    draw.text((dx1 + 80, dy1 + 200), "GRADE A (COMPLIANT)", font=font_stat_val, fill=(16, 185, 129))

    draw.text((dx1 + 550, dy1 + 160), "TOTAL ENCROACHMENTS:", font=font_mono_small, fill=(71, 85, 105))
    draw.text((dx1 + 550, dy1 + 200), "114.70 m²", font=font_stat_val, fill=(225, 29, 72))

    draw.text((dx1 + 50, dy1 + 280), "ITEMIZED DISCREPANCY AUDIT LOGS (LOCAL UTM ZONE 44N):", font=font_mono_small, fill=(15, 23, 42))
    headers = ["FEATURE ID", "STRUCTURE TYPE", "ENCROACHMENT", "PENETRATION", "SEVERITY"]
    for h_idx, h in enumerate(headers):
        draw.text((dx1 + 50 + h_idx * 180, ry := dy1 + 315), h, font=font_mono_small, fill=(100, 116, 139))
    draw.line([(dx1 + 50, dy1 + 345), (dx2 - 50, dy1 + 345)], fill=(203, 213, 225), width=1)

    rows = [
        ("V-001", "Commercial Masonry", "84.20 m²", "6.20 m", "CRITICAL"),
        ("V-002", "Boundary Wall", "18.50 m²", "1.80 m", "MEDIUM"),
        ("V-003", "Concrete Ramp", "12.00 m²", "0.90 m", "LOW")
    ]
    for r_idx, row in enumerate(rows):
        ry = dy1 + 370 + r_idx * 45
        for c_idx, cell in enumerate(row):
            col = (225, 29, 72) if cell == "CRITICAL" else (15, 23, 42)
            draw.text((dx1 + 50 + c_idx * 180, ry), cell, font=font_mono_small, fill=col)

    stamp_t = clamp((progress - 0.4) * 2.5)
    if stamp_t > 0:
        stamp_scale = ease_out_back(stamp_t)
        stamp_cx, stamp_cy = dx2 - 200, dy1 + 560
        sr = max(1, int(80 * stamp_scale))
        draw.ellipse([(stamp_cx - sr, stamp_cy - sr), (stamp_cx + sr, stamp_cy + sr)], outline=(217, 119, 6), width=4)
        if sr > 12:
            draw.ellipse([(stamp_cx - sr + 8, stamp_cy - sr + 8), (stamp_cx + sr - 8, stamp_cy + sr - 8)], outline=(217, 119, 6), width=2)
            draw.text((stamp_cx, stamp_cy - 15), "MUNICIPAL AUDIT", font=font_mono_small, fill=(217, 119, 6), anchor="mm")
            draw.text((stamp_cx, stamp_cy + 15), "APPROVED", font=font_card_title, fill=(217, 119, 6), anchor="mm")

    draw_caption_bar(draw, "STEP 3: Compiles formal municipal compliance certificates with digital seals in one click")
    return np.array(img)

def render_scene_7(frame_idx, progress):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)
    draw_bg_grid(draw, frame_idx)

    cx, cy = WIDTH // 2, HEIGHT // 2 - 30
    draw_rounded_rect(draw, (cx - 520, cy - 270, cx + 520, cy + 270), radius=20, fill=BG_CARD, outline=CYAN, width=2)

    draw.text((cx, cy - 180), "CITYTWIN AI", font=font_hero, fill=WHITE, anchor="mm")
    draw.text((cx, cy - 110), "Empowering Smarter, Faster, Compliant Infrastructure", font=font_subtitle, fill=LIGHT_GRAY, anchor="mm")

    stats = [
        ("85%", "Faster RoW Clearance"),
        ("0%", "Hallucination Math"),
        ("100%", "Foliage Accountability")
    ]
    for idx, (val, desc) in enumerate(stats):
        sx = cx - 360 + idx * 360
        draw.text((sx, cy - 20), val, font=font_stat_val, fill=CYAN, anchor="mm")
        draw.text((sx, cy + 25), desc, font=font_body, fill=GRAY, anchor="mm")

    draw.line([(cx - 420, cy + 70), (cx + 420, cy + 70)], fill=BORDER_COLOR, width=1)

    draw_rounded_rect(draw, (cx - 400, cy + 110, cx + 400, cy + 180), radius=10, fill=(15, 23, 42), outline=EMERALD, width=1)
    draw.text((cx, cy + 145), "GITHUB: https://github.com/G456-max/citytwin-ai", font=font_mono, fill=EMERALD, anchor="mm")

    draw_caption_bar(draw, "CITYTWIN AI • Next-Generation Municipal Infrastructure Verification Platform")
    return np.array(img)

# Scene scripts & narrations
SCENE_SCRIPTS = [
    ("Scene 1", "Welcome to CityTwin AI. In the historic city of Rajamahendravaram, Andhra Pradesh, municipal engineers face a critical challenge along the Godavari River highway corridor.", render_scene_1),
    ("Scene 2", "To widen the highway to four lanes, the city must identify illegal property encroachments, align engineering blueprints with satellite GPS, and quantify roadside tree canopy clearing for environmental approvals. Traditional on-ground surveys take weeks and spark legal disputes, while standard generative AI tools hallucinate fake roads.", render_scene_2),
    ("Scene 3", "CityTwin AI solves this through a dual-engine architecture. First, our Three-Point Ground Control Point Snapping solver uses affine matrix math to automatically lock unreferenced CAD blueprints onto real-world WGS84 GPS benchmarks.", render_scene_3),
    ("Scene 4", "Second, in Step One, the deterministic math engine reprojects drone orthomosaics into localized metric UTM Zone 44N coordinates. It performs exact polygon intersection math, identifying structural encroachments down to the centimeter, calculating total square meter overlap and maximum penetration depth with zero hallucinations. Simultaneously, computer vision HSV vegetation filters isolate tree crowns and calculate exact forestry canopy loss.", render_scene_4),
    ("Scene 5", "Third, in Step Two, our Blueprint-Locked Generative Engine uses ControlNet depth conditioning tied directly to the elevation model. It renders photorealistic highway textures, crisp lane markings, and curbs under daylight, monsoon, or night conditions, strictly locked to the engineered geometry.", render_scene_5),
    ("Scene 6", "Finally, in Step Three, CityTwin AI generates a formal municipal compliance audit PDF certificate, complete with itemized discrepancy logs, scorecards, and digital approval seals in a single click.", render_scene_6),
    ("Scene 7", "CityTwin AI: Transforming municipal infrastructure verification with mathematically grounded spatial intelligence.", render_scene_7)
]

def synthesize_scene_audios():
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    speaker.Rate = -1
    speaker.Volume = 100
    
    scene_durations = []
    wav_files = []
    
    for idx, (name, text, _) in enumerate(SCENE_SCRIPTS):
        wav_path = f"scene_{idx+1}_audio.wav"
        stream = win32com.client.Dispatch("SAPI.SpFileStream")
        stream.Open(wav_path, 3, False)
        speaker.AudioOutputStream = stream
        speaker.Speak(text)
        stream.Close()
        
        # Read duration
        with wave.open(wav_path, 'r') as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / float(rate)
            scene_durations.append(duration + 0.8)  # add 0.8s buffer for smooth pacing
            wav_files.append(wav_path)
            print(f"Generated {name} audio: {duration:.2f}s (Allocating {scene_durations[-1]:.2f}s)")
            
    return scene_durations, wav_files

def main():
    print("--------------------------------------------------")
    print("CITYTWIN AI • MASTER ANIMATED VIDEO BUILDER")
    print("--------------------------------------------------")
    
    # 1. Synthesize audio per scene
    scene_durations, wav_files = synthesize_scene_audios()
    
    # 2. Combine WAV audio files into a single master audio track
    print("Assembling master audio track...")
    combined_frames = []
    rate = None
    nchannels = None
    sampwidth = None
    for w_file, dur in zip(wav_files, scene_durations):
        with wave.open(w_file, 'r') as wf:
            rate = wf.getframerate()
            nchannels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            data = wf.readframes(wf.getnframes())
            combined_frames.append(data)
            # Add silence padding for the buffer
            silence_samples = int(0.8 * rate)
            silence_bytes = b'\x00' * (silence_samples * nchannels * sampwidth)
            combined_frames.append(silence_bytes)
            
    with wave.open(TEMP_AUDIO, 'wb') as wf:
        wf.setnchannels(nchannels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(rate)
        wf.writeframes(b"".join(combined_frames))
        
    print(f"Master audio track generated: {TEMP_AUDIO}")
    
    # 3. Render video frames synchronized exactly to audio duration
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(TEMP_VIDEO, fourcc, FPS, (WIDTH, HEIGHT))
    
    global_frame_idx = 0
    for idx, (_, _, render_func) in enumerate(SCENE_SCRIPTS):
        dur = scene_durations[idx]
        total_scene_frames = int(dur * FPS)
        print(f"Rendering Scene {idx+1}/{len(SCENE_SCRIPTS)} ({total_scene_frames} frames)...")
        for f in range(total_scene_frames):
            prog = f / float(total_scene_frames)
            frame_rgb = render_func(global_frame_idx, prog)
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            out.write(frame_bgr)
            global_frame_idx += 1
            
    out.release()
    print(f"Raw video rendered: {TEMP_VIDEO} ({global_frame_idx} frames)")
    
    # 4. Mux video and audio using imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    print(f"Multiplexing audio and video into {FINAL_OUTPUT}...")
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", TEMP_VIDEO,
        "-i", TEMP_AUDIO,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        FINAL_OUTPUT
    ]
    subprocess.run(cmd, check=True)
    
    # Cleanup temp wavs
    for w in wav_files:
        if os.path.exists(w):
            os.remove(w)
    if os.path.exists(TEMP_VIDEO):
        os.remove(TEMP_VIDEO)
    if os.path.exists(TEMP_AUDIO):
        os.remove(TEMP_AUDIO)
        
    print(f"SUCCESS: Master presentation video generated at {FINAL_OUTPUT}!")

if __name__ == "__main__":
    main()
