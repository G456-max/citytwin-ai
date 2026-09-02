import os
import sys
import math
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

WIDTH = 1920
HEIGHT = 1080
FPS = 30
OUTPUT_FILE = "citytwin_ai_presentation.mp4"

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
font_hero = ImageFont.truetype(str(FONT_DIR / "segoeuib.ttf"), 78)
font_title = ImageFont.truetype(str(FONT_DIR / "segoeuib.ttf"), 48)
font_subtitle = ImageFont.truetype(str(FONT_DIR / "segoeui.ttf"), 26)
font_card_title = ImageFont.truetype(str(FONT_DIR / "segoeuib.ttf"), 26)
font_body = ImageFont.truetype(str(FONT_DIR / "segoeui.ttf"), 20)
font_mono = ImageFont.truetype(str(FONT_DIR / "consolab.ttf"), 22)
font_mono_small = ImageFont.truetype(str(FONT_DIR / "consolab.ttf"), 16)
font_stamp = ImageFont.truetype(str(FONT_DIR / "segoeuib.ttf"), 36)
font_stat_val = ImageFont.truetype(str(FONT_DIR / "segoeuib.ttf"), 42)

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
    draw.text((80, 45), step_text, font=font_mono_small, fill=CYAN)
    draw.text((80, 75), title_text, font=font_title, fill=WHITE)
    draw.line([(80, 145), (1840, 145)], fill=BORDER_COLOR, width=2)

def draw_bg_grid(draw, frame_idx):
    for x in range(40, WIDTH, 60):
        for y in range(40, HEIGHT, 60):
            draw.point((x, y), fill=(22, 30, 46))
            
    # Subtle moving scan line
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

def render_scene_1_intro(frame_idx, progress):
    # Frames 0 to 240 (0 - 8s)
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)
    draw_bg_grid(draw, frame_idx)

    # Expanding radar rings in center
    cx, cy = WIDTH // 2, HEIGHT // 2 - 40
    for r_offset in [0, 80, 160, 240, 320]:
        radius = int((frame_idx * 2 + r_offset) % 450)
        alpha = int(255 * (1.0 - radius / 450.0))
        c_val = int(56 * (alpha / 255.0))
        draw.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)], outline=(c_val // 2, c_val, int(248 * (alpha / 255.0))), width=1)

    # Logo Box
    box_w, box_h = 1050, 480
    bx1 = cx - box_w // 2
    by1 = cy - box_h // 2
    draw_rounded_rect(draw, (bx1, by1, bx1 + box_w, by1 + box_h), radius=20, fill=(13, 18, 30), outline=CYAN, width=2)

    # Title & Content
    tag_t = clamp((progress - 0.15) * 3)
    if tag_t > 0:
        draw_rounded_rect(draw, (cx - 180, by1 + 40, cx + 180, by1 + 75), radius=8, fill=(15, 23, 42), outline=(30, 58, 138), width=1)
        draw.text((cx, by1 + 57), "NEXT-GEN GEOSPATIAL INTELLIGENCE", font=font_mono_small, fill=CYAN, anchor="mm")

    hero_t = clamp((progress - 0.25) * 3)
    if hero_t > 0:
        draw.text((cx, cy - 35), "CITYTWIN AI", font=font_hero, fill=WHITE, anchor="mm")
        draw.text((cx, cy + 35), "Dual-Core Municipal Highway Compliance & Generative Verification", font=font_subtitle, fill=LIGHT_GRAY, anchor="mm")

    badges_t = clamp((progress - 0.4) * 3)
    if badges_t > 0:
        badges = [
            ("0% AI Hallucination Math", EMERALD),
            ("Blueprint-Locked Diffusion", CYAN),
            ("Automated Canopy Auditing", GOLD),
            ("Instant Municipal PDF Reports", PURPLE)
        ]
        badge_x = cx - 440
        badge_y = cy + 120
        for text, color in badges:
            draw_rounded_rect(draw, (badge_x, badge_y, badge_x + 210, badge_y + 45), radius=8, fill=(17, 24, 39), outline=color, width=1)
            draw.text((badge_x + 105, badge_y + 22), text, font=font_mono_small, fill=WHITE, anchor="mm")
            badge_x += 225

    return np.array(img)

def render_scene_2_problem(frame_idx, progress):
    # Frames 240 to 480 (8 - 16s)
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)
    draw_bg_grid(draw, frame_idx)
    draw_header(draw, "THE MUNICIPAL HIGHWAY EXPANSION BOTTLENECK", "THE PROBLEM • TRADITIONAL SURVEY LIMITATIONS")

    cards = [
        ("01", "Unauthorized Encroachments", "Illegal houses, shops, and fences encroaching on statutory highway Right-of-Way. Physical discovery takes weeks of surveying.", ROSE),
        ("02", "CAD vs. GPS Datum Shifts", "CAD blueprints exist in local (X, Y) coordinates and fail to align with real-world satellite WGS84 GPS benchmarks.", GOLD),
        ("03", "Undocumented Tree Removal", "Environmental forestry clearances stall projects for months due to slow, manual tree counting and canopy estimates.", EMERALD),
        ("04", "Abstract Wireframe Confusion", "Civil CAD wireframes are incomprehensible to citizens and municipal leaders, while generic AI hallucinates unbuildable roads.", CYAN)
    ]

    for idx, (num, title, desc, col) in enumerate(cards):
        card_t = clamp((progress - idx * 0.15) * 3)
        if card_t <= 0:
            continue
        eased_t = ease_in_out(card_t)
        card_x = 80 + idx * 445
        target_y = 200
        start_y = 350
        card_y = int(lerp(start_y, target_y, eased_t))

        draw_rounded_rect(draw, (card_x, card_y, card_x + 420, card_y + 700), radius=16, fill=BG_CARD, outline=col, width=2)
        
        # Number badge
        draw_rounded_rect(draw, (card_x + 25, card_y + 30, card_x + 75, card_y + 80), radius=10, fill=(15, 23, 42), outline=col, width=1)
        draw.text((card_x + 50, card_y + 55), num, font=font_card_title, fill=col, anchor="mm")

        # Warning icon bar
        draw.rectangle([card_x + 25, card_y + 105, card_x + 395, card_y + 107], fill=BORDER_COLOR)

        # Title & Description
        draw.text((card_x + 25, card_y + 130), title, font=font_card_title, fill=WHITE)
        
        # Word wrap desc
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
            draw.text((card_x + 25, card_y + 200 + l_idx * 32), line, font=font_body, fill=GRAY)

    return np.array(img)

def render_scene_3_architecture(frame_idx, progress):
    # Frames 480 to 720 (16 - 24s)
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)
    draw_bg_grid(draw, frame_idx)
    draw_header(draw, "DUAL-CORE PARADIGM: MATH + GENERATIVE VERIFICATION", "CORE ARCHITECTURE • ZERO HALLUCINATION")

    # Left Card: Deterministic Math Core
    t_left = clamp(progress * 2)
    if t_left > 0:
        lx = 80
        ly = int(lerp(260, 200, ease_in_out(t_left)))
        draw_rounded_rect(draw, (lx, ly, lx + 840, ly + 720), radius=20, fill=BG_CARD, outline=CYAN, width=2)
        
        draw_rounded_rect(draw, (lx + 35, ly + 35, lx + 360, ly + 75), radius=8, fill=(15, 23, 42), outline=CYAN, width=1)
        draw.text((lx + 45, ly + 55), "CORE 1: DETERMINISTIC MATH ENGINE", font=font_mono_small, fill=CYAN, anchor="lm")
        
        draw.text((lx + 35, ly + 110), "Metric UTM Spatial Compliance", font=font_card_title, fill=WHITE)
        draw.text((lx + 35, ly + 155), "• 3-Point GCP Affine Snapping Matrix Solver", font=font_body, fill=LIGHT_GRAY)
        draw.text((lx + 35, ly + 195), "• Reprojection to Local Metric UTM Zone 44N (EPSG:32644)", font=font_body, fill=LIGHT_GRAY)
        draw.text((lx + 35, ly + 235), "• Exact Polygon Intersection: Im = Sm ∩ Rm", font=font_body, fill=LIGHT_GRAY)
        draw.text((lx + 35, ly + 275), "• Maximum Intrusion Penetration Depth (D_max)", font=font_body, fill=LIGHT_GRAY)
        draw.text((lx + 35, ly + 315), "• HSV Green Canopy Indexing: 35 <= H <= 85", font=font_body, fill=LIGHT_GRAY)

        # Formula Highlight Box
        draw_rounded_rect(draw, (lx + 35, ly + 380, lx + 805, ly + 660), radius=12, fill=(10, 15, 26), outline=BORDER_COLOR, width=1)
        draw.text((lx + 60, ly + 420), "MATHEMATICAL FORMULATION:", font=font_mono_small, fill=GOLD)
        draw.text((lx + 60, ly + 470), "Area (m2) = DoubleIntegral_{Im} dx dy", font=font_mono, fill=CYAN)
        draw.text((lx + 60, ly + 530), "D_max = max_{pj in Im} dist(pj, Bound_Rm)", font=font_mono, fill=CYAN)
        draw.text((lx + 60, ly + 590), "Vegetation Mask = HSV[35..85, 20..255, 20..255]", font=font_mono, fill=EMERALD)

    # Right Card: Blueprint-Locked Generative Engine
    t_right = clamp((progress - 0.2) * 2)
    if t_right > 0:
        rx = 980
        ry = int(lerp(260, 200, ease_in_out(t_right)))
        draw_rounded_rect(draw, (rx, ry, rx + 840, ry + 720), radius=20, fill=BG_CARD, outline=PURPLE, width=2)
        
        draw_rounded_rect(draw, (rx + 35, ry + 35, rx + 400, ry + 75), radius=8, fill=(15, 23, 42), outline=PURPLE, width=1)
        draw.text((rx + 45, ry + 55), "CORE 2: BLUEPRINT-LOCKED DIFFUSION", font=font_mono_small, fill=PURPLE, anchor="lm")
        
        draw.text((rx + 35, ry + 110), "Geometry-Constrained Visual Twin", font=font_card_title, fill=WHITE)
        draw.text((rx + 35, ry + 155), "• Stable Diffusion + ControlNet Depth Condition Cages", font=font_body, fill=LIGHT_GRAY)
        draw.text((rx + 35, ry + 195), "• Normalizes Photogrammetric DEM Elevation Buffers", font=font_body, fill=LIGHT_GRAY)
        draw.text((rx + 35, ry + 235), "• Zero Hallucination: Preserves Exact Engineering Widths", font=font_body, fill=LIGHT_GRAY)
        draw.text((rx + 35, ry + 275), "• Multi-Weather Synthesizer (Daylight, Night, Monsoon)", font=font_body, fill=LIGHT_GRAY)
        draw.text((rx + 35, ry + 315), "• Deterministic Procedural OpenCV Fallback Engine", font=font_body, fill=LIGHT_GRAY)

        # Style Presets Box
        draw_rounded_rect(draw, (rx + 35, ry + 380, rx + 805, ry + 660), radius=12, fill=(10, 15, 26), outline=BORDER_COLOR, width=1)
        draw.text((rx + 60, ry + 420), "ENVIRONMENTAL SCENARIO PRESETS:", font=font_mono_small, fill=GOLD)
        presets = [
            ("Realistic Daylight", "4-lane asphalt, crisp white markings, curbs, trees"),
            ("Nighttime Illumination", "Streetlights glow, headlights, night contrast"),
            ("Monsoon Weather", "Wet asphalt reflections, overcast sky, water runoffs"),
            ("Eco-Green Corridor", "Vertical gardens, green median barriers, potted plants")
        ]
        for p_idx, (p_title, p_sub) in enumerate(presets):
            draw.text((rx + 60, ry + 465 + p_idx * 46), p_title, font=font_mono_small, fill=PURPLE)
            draw.text((rx + 320, ry + 465 + p_idx * 46), p_sub, font=font_body, fill=GRAY)

    return np.array(img)

def render_scene_4_step1_audit(frame_idx, progress):
    # Frames 720 to 1050 (24 - 35s)
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)
    draw_bg_grid(draw, frame_idx)
    draw_header(draw, "STEP 1: AUTONOMOUS GIS COMPLIANCE AUDITING", "LIVE DASHBOARD • SPATIAL DISCREPANCY DETECTION")

    # Left Sidebar: Triage Cards
    draw_rounded_rect(draw, (80, 180, 420, 960), radius=16, fill=BG_CARD, outline=BORDER_COLOR, width=1)
    draw.text((105, 210), "AUDIT TRIAGE LOGS", font=font_mono_small, fill=CYAN)
    
    triage = [
        ("V-01: Commercial Wall", "Area: 84.20 m2 | Depth: 6.2m", "CRITICAL", ROSE),
        ("V-02: Boundary Fence", "Area: 18.50 m2 | Depth: 1.8m", "MEDIUM", GOLD),
        ("V-03: Concrete Porch", "Area: 12.00 m2 | Depth: 0.9m", "LOW", CYAN),
        ("T-01: Tree Canopy Group", "Clearance: 14 Trees | 320 m2", "FORESTRY", EMERALD)
    ]
    for idx, (t_title, t_desc, t_sev, t_col) in enumerate(triage):
        ty = 250 + idx * 165
        draw_rounded_rect(draw, (100, ty, 400, ty + 145), radius=12, fill=(11, 15, 25), outline=BORDER_COLOR, width=1)
        draw.text((115, ty + 20), t_title, font=font_card_title, fill=WHITE)
        draw.text((115, ty + 60), t_desc, font=font_body, fill=GRAY)
        draw_rounded_rect(draw, (115, ty + 100, 230, ty + 130), radius=6, fill=(15, 23, 42), outline=t_col, width=1)
        draw.text((172, ty + 115), t_sev, font=font_mono_small, fill=t_col, anchor="mm")

    # Center/Right: Interactive Map Viewport
    mx, my, mw, mh = 460, 180, 1380, 780
    draw_rounded_rect(draw, (mx, my, mx + mw, my + mh), radius=16, fill=(15, 20, 32), outline=BORDER_COLOR, width=1)

    # Top Telemetry Bar inside map
    draw.rectangle([mx, my, mx + mw, my + 60], fill=(10, 14, 22))
    draw.line([(mx, my + 60), (mx + mw, my + 60)], fill=BORDER_COLOR, width=1)
    
    stats = [
        ("COMPLIANCE GRADE", "A", EMERALD),
        ("TOTAL VIOLATIONS", "3 Detected", ROSE),
        ("ENCROACHMENT AREA", "114.70 m2", ROSE),
        ("CANOPY CLEARANCE", "320 m2 (14 Trees)", EMERALD)
    ]
    for s_idx, (label, val, col) in enumerate(stats):
        sx = mx + 30 + s_idx * 330
        draw.text((sx, my + 18), label + ":", font=font_mono_small, fill=GRAY)
        draw.text((sx + 170, my + 18), val, font=font_mono_small, fill=col)

    # Road Corridor (Diagonal Highway)
    road_poly = [(mx + 200, my + mh - 50), (mx + 450, my + 100), (mx + 850, my + 100), (mx + 600, my + mh - 50)]
    draw.polygon(road_poly, fill=(28, 38, 58))
    # Sanctioned RoW Boundary lines (Cyan)
    draw.line([road_poly[0], road_poly[1]], fill=CYAN, width=3)
    draw.line([road_poly[3], road_poly[2]], fill=CYAN, width=3)
    draw.text((mx + 300, my + mh - 120), "SANCTIONED RIGHT-OF-WAY (12m WIDE)", font=font_mono_small, fill=CYAN)

    # Buildings
    # Non-encroaching building (Gray)
    draw.polygon([(mx + 100, my + 300), (mx + 250, my + 300), (mx + 250, my + 450), (mx + 100, my + 450)], fill=(40, 50, 70), outline=GRAY)
    
    # Encroaching building (Red overlap)
    bldg_viol = [(mx + 380, my + 250), (mx + 560, my + 250), (mx + 560, my + 420), (mx + 380, my + 420)]
    draw.polygon(bldg_viol, fill=(45, 30, 40), outline=GRAY)
    
    # Intersecting Encroachment zone (Flashing Rose)
    pulse = (math.sin(frame_idx * 0.2) + 1.0) / 2.0
    encroach_poly = [(mx + 420, my + 250), (mx + 560, my + 250), (mx + 560, my + 420), (mx + 470, my + 420)]
    encroach_fill = (int(180 + 75 * pulse), int(20 + 20 * pulse), int(50 + 20 * pulse))
    draw.polygon(encroach_poly, fill=encroach_fill, outline=ROSE, width=2)

    # Callout popup box
    callout_x, callout_y = mx + 620, my + 280
    draw.line([(mx + 520, my + 320), (callout_x, callout_y + 40)], fill=ROSE, width=2)
    draw_rounded_rect(draw, (callout_x, callout_y, callout_x + 360, callout_y + 110), radius=10, fill=(10, 15, 25), outline=ROSE, width=2)
    draw.text((callout_x + 20, callout_y + 20), "ENCROACHMENT DETECTED", font=font_mono_small, fill=ROSE)
    draw.text((callout_x + 20, callout_y + 50), "• Overlap Area: 84.20 m2", font=font_body, fill=WHITE)
    draw.text((callout_x + 20, callout_y + 75), "• Max Intrusion: 6.2 meters", font=font_body, fill=GOLD)

    # Green Canopy Loss zone
    draw.ellipse([(mx + 700, my + 500), (mx + 860, my + 660)], fill=(20, 60, 40), outline=EMERALD, width=2)
    draw.text((mx + 780, my + 580), "CANOPY LOSS\n320 m2", font=font_mono_small, fill=EMERALD, anchor="mm")

    return np.array(img)

def render_scene_5_step2_render(frame_idx, progress):
    # Frames 1050 to 1380 (35 - 46s)
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)
    draw_bg_grid(draw, frame_idx)
    draw_header(draw, "STEP 2: BLUEPRINT-LOCKED GENERATIVE VISUALIZER", "INTERACTIVE WIPE SLIDER • CONTROLNET CAD DIFFUSION")

    sx, sy, sw, sh = 120, 180, 1680, 780
    draw_rounded_rect(draw, (sx, sy, sx + sw, sy + sh), radius=16, fill=(15, 20, 32), outline=BORDER_COLOR, width=1)

    # Calculate wiping slider position (sweeps back and forth)
    slider_pct = (math.sin((progress * 4.0) * math.pi) + 1.0) / 2.0 * 0.6 + 0.2
    split_x = int(sx + sw * slider_pct)

    # Left Side: Baseline Aerial View
    draw.rectangle([sx + 5, sy + 5, split_x, sy + sh - 5], fill=(30, 42, 55))
    draw.text((sx + 50, sy + sh - 80), "BASELINE: RAW DRONE ORTHOMOSAIC", font=font_mono, fill=EMERALD)
    draw.text((sx + 50, sy + sh - 45), "Unpaved dirt verges, encroaching structures, irregular boundaries", font=font_body, fill=GRAY)

    # Right Side: AI Synthesized CAD View
    draw.rectangle([split_x, sy + 5, sx + sw - 5, sy + sh - 5], fill=(20, 30, 45))
    draw.text((split_x + 50, sy + sh - 80), "SYNTHESIZED: GEOMETRY-LOCKED ROADWAY", font=font_mono, fill=CYAN)
    draw.text((split_x + 50, sy + sh - 45), "Modern 4-lane asphalt, crisp lane markings, streetlights & curbs", font=font_body, fill=GRAY)

    # Draw simulated road graphic through the canvas
    mid_y = sy + sh // 2 - 40
    # Left road (rough)
    draw.polygon([(sx + 5, mid_y + 120), (split_x, mid_y + 120), (split_x, mid_y - 120), (sx + 5, mid_y - 120)], fill=(45, 52, 60))
    # Right road (modern highway with lanes)
    draw.polygon([(split_x, mid_y + 120), (sx + sw - 5, mid_y + 120), (sx + sw - 5, mid_y - 120), (split_x, mid_y - 120)], fill=(18, 22, 30))
    # Crisp white road stripes on right
    for stripe_x in range(split_x + 30, sx + sw - 60, 90):
        draw.line([(stripe_x, mid_y), (stripe_x + 50, mid_y)], fill=WHITE, width=4)
        draw.line([(stripe_x, mid_y - 60), (stripe_x + 50, mid_y - 60)], fill=(240, 240, 240), width=2)
        draw.line([(stripe_x, mid_y + 60), (stripe_x + 50, mid_y + 60)], fill=(240, 240, 240), width=2)

    # Split Wipe Handle (Cyan vertical line with circle grip)
    draw.line([(split_x, sy + 5), (split_x, sy + sh - 5)], fill=CYAN, width=3)
    draw.ellipse([(split_x - 24, sy + sh // 2 - 24), (split_x + 24, sy + sh // 2 + 24)], fill=(15, 23, 42), outline=CYAN, width=2)
    draw.text((split_x, sy + sh // 2), "< >", font=font_mono_small, fill=CYAN, anchor="mm")

    # Presets Floating Bar on top right
    draw_rounded_rect(draw, (sx + sw - 580, sy + 30, sx + sw - 30, sy + 80), radius=10, fill=(10, 15, 25), outline=BORDER_COLOR, width=1)
    draw.text((sx + sw - 560, sy + 55), "STYLE PRESET: REALISTIC DAYLIGHT (8K RES)", font=font_mono_small, fill=GOLD, anchor="lm")

    return np.array(img)

def render_scene_6_step3_pdf(frame_idx, progress):
    # Frames 1380 to 1650 (46 - 55s)
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)
    draw_bg_grid(draw, frame_idx)
    draw_header(draw, "STEP 3: ONE-CLICK MUNICIPAL PDF REPORT", "OFFICIAL STATUTORY COMPLIANCE CERTIFICATION")

    # Document Paper mockup sliding up
    doc_t = clamp(progress * 2)
    doc_y = int(lerp(280, 190, ease_out_back(doc_t)))
    dx1, dx2 = 460, 1460
    dy1, dy2 = doc_y, doc_y + 780

    # Shadow
    draw_rounded_rect(draw, (dx1 + 10, dy1 + 10, dx2 + 10, dy2 + 10), radius=16, fill=(5, 8, 14))
    # Paper Body
    draw_rounded_rect(draw, (dx1, dy1, dx2, dy2), radius=16, fill=(248, 250, 252), outline=(203, 213, 225), width=2)

    # Document Header
    draw.text((dx1 + 50, dy1 + 45), "MUNICIPAL HIGHWAY STATUTORY COMPLIANCE REPORT", font=font_card_title, fill=(15, 23, 42))
    draw.text((dx1 + 50, dy1 + 85), "Project: Rajamahendravaram Godavari Corridor Expansion • Ref: MH-2026-AP", font=font_body, fill=(71, 85, 105))
    draw.line([(dx1 + 50, dy1 + 125), (dx2 - 50, dy1 + 125)], fill=(203, 213, 225), width=2)

    # Executive Scorecard Table
    draw.rectangle([dx1 + 50, dy1 + 150, dx2 - 50, dy1 + 270], fill=(241, 245, 249))
    draw.text((dx1 + 80, dy1 + 180), "STATUTORY CLEARANCE GRADE:", font=font_mono_small, fill=(71, 85, 105))
    draw.text((dx1 + 80, dy1 + 220), "GRADE A (COMPLIANT)", font=font_stat_val, fill=(16, 185, 129))

    draw.text((dx1 + 550, dy1 + 180), "TOTAL ENCROACHMENTS:", font=font_mono_small, fill=(71, 85, 105))
    draw.text((dx1 + 550, dy1 + 220), "114.70 m2", font=font_stat_val, fill=(225, 29, 72))

    # Itemized Table Mockup
    draw.text((dx1 + 50, dy1 + 300), "ITEMIZED DISCREPANCY AUDIT LOGS (LOCAL UTM ZONE 44N):", font=font_mono_small, fill=(15, 23, 42))
    headers = ["FEATURE ID", "STRUCTURE TYPE", "ENCROACHMENT", "PENETRATION", "SEVERITY"]
    for h_idx, h in enumerate(headers):
        draw.text((dx1 + 50 + h_idx * 180, dy1 + 335), h, font=font_mono_small, fill=(100, 116, 139))
    draw.line([(dx1 + 50, dy1 + 365), (dx2 - 50, dy1 + 365)], fill=(203, 213, 225), width=1)

    rows = [
        ("V-001", "Commercial Masonry", "84.20 m2", "6.20 m", "CRITICAL"),
        ("V-002", "Boundary Wall", "18.50 m2", "1.80 m", "MEDIUM"),
        ("V-003", "Concrete Ramp", "12.00 m2", "0.90 m", "LOW")
    ]
    for r_idx, row in enumerate(rows):
        ry = dy1 + 390 + r_idx * 45
        for c_idx, cell in enumerate(row):
            col = (225, 29, 72) if cell == "CRITICAL" else (15, 23, 42)
            draw.text((dx1 + 50 + c_idx * 180, ry), cell, font=font_mono_small, fill=col)

    # Stamp Animation
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

    return np.array(img)

def render_scene_7_outro(frame_idx, progress):
    # Frames 1650 to 1800 (55 - 60s)
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(img)
    draw_bg_grid(draw, frame_idx)

    cx, cy = WIDTH // 2, HEIGHT // 2

    # Title Box
    draw_rounded_rect(draw, (cx - 500, cy - 260, cx + 500, cy + 260), radius=20, fill=BG_CARD, outline=CYAN, width=2)

    draw.text((cx, cy - 180), "CITYTWIN AI", font=font_hero, fill=WHITE, anchor="mm")
    draw.text((cx, cy - 110), "Empowering Smarter, Faster, Compliant Infrastructure", font=font_subtitle, fill=LIGHT_GRAY, anchor="mm")

    # Metrics Summary
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

    # GitHub Repo Banner
    draw_rounded_rect(draw, (cx - 380, cy + 110, cx + 380, cy + 180), radius=10, fill=(15, 23, 42), outline=EMERALD, width=1)
    draw.text((cx, cy + 145), "GITHUB: https://github.com/G456-max/citytwin-ai", font=font_mono, fill=EMERALD, anchor="mm")

    return np.array(img)

def main():
    print(f"Generating video: {OUTPUT_FILE} ({WIDTH}x{HEIGHT} at {FPS} FPS)...")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(OUTPUT_FILE, fourcc, FPS, (WIDTH, HEIGHT))

    scenes = [
        (0, 240, render_scene_1_intro),
        (240, 480, render_scene_2_problem),
        (480, 720, render_scene_3_architecture),
        (720, 1050, render_scene_4_step1_audit),
        (1050, 1380, render_scene_5_step2_render),
        (1380, 1650, render_scene_6_step3_pdf),
        (1650, 1800, render_scene_7_outro)
    ]

    total_rendered = 0
    for s_idx, (start_f, end_f, render_func) in enumerate(scenes):
        count = end_f - start_f
        print(f"Rendering Scene {s_idx + 1}/{len(scenes)} (Frames {start_f} to {end_f})...")
        for f in range(start_f, end_f):
            prog = (f - start_f) / float(count)
            frame_rgb = render_func(f, prog)
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            out.write(frame_bgr)
            total_rendered += 1

    out.release()
    print(f"SUCCESS: Animated video generated and saved to {OUTPUT_FILE} ({total_rendered} frames)!")

if __name__ == "__main__":
    main()
