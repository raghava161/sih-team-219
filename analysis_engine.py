import os
import cv2
import numpy as np

class AnalysisEngine:
    def __init__(self):
        pass

    def run_ndvi(self, input_image_path, output_image_path):
        img_bgr = cv2.imread(input_image_path)
        if img_bgr is None:
            raise ValueError("Could not read image for NDVI analysis.")

        b, g, r = cv2.split(img_bgr.astype(np.float32))

        nir_approx = g * 1.15
        denominator = (nir_approx + r)
        denominator[denominator == 0] = 1e-5
        ndvi = (nir_approx - r) / denominator
        ndvi = np.clip(ndvi, -1.0, 1.0)

        # Build a scientifically correct NDVI colormap manually:
        # High NDVI (healthy vegetation) -> Green (0, 200, 0)
        # Moderate NDVI (crops, sparse veg) -> Yellow (0, 220, 220)
        # Low/Negative NDVI (barren, water, urban) -> Red (0, 0, 220)
        high_veg_mask = ndvi > 0.30
        mod_veg_mask = (ndvi > 0.08) & (ndvi <= 0.30)
        barren_mask = ndvi <= 0.08

        h, w = ndvi.shape
        heatmap = np.zeros((h, w, 3), dtype=np.uint8)
        heatmap[barren_mask]  = (0,   0, 220)    # BGR red   = barren/water
        heatmap[mod_veg_mask] = (0, 220, 220)    # BGR yellow = moderate vegetation
        heatmap[high_veg_mask] = (0, 200,   0)   # BGR green  = dense healthy vegetation

        total_pixels = ndvi.size
        high_veg_pct = round((np.sum(high_veg_mask) / total_pixels) * 100, 1)
        mod_veg_pct = round((np.sum(mod_veg_mask) / total_pixels) * 100, 1)
        barren_pct = round((np.sum(barren_mask) / total_pixels) * 100, 1)
        mean_ndvi = round(float(np.mean(ndvi)), 2)

        legend_img = self._add_overlay_legend(heatmap, [
            ("High Vegetation (>0.3)", (0, 255, 0)),
            ("Moderate Veg (0.1 - 0.3)", (255, 255, 0)),
            ("Barren / Water (<0.1)", (0, 0, 255))
        ], "🌿 NDVI VEGETATION INDEX MAP")

        cv2.imwrite(output_image_path, legend_img)

        return {
            "module": "ndvi",
            "title": "NDVI Vegetation Health Index",
            "stats": [
                {"label": "Dense Healthy Vegetation", "value": f"{high_veg_pct}%", "color": "#00ff88"},
                {"label": "Moderate / Crop Vegetation", "value": f"{mod_veg_pct}%", "color": "#ffee00"},
                {"label": "Barren Soil / Water / Urban", "value": f"{barren_pct}%", "color": "#ff4d4d"},
                {"label": "Mean NDVI Index Score", "value": f"{mean_ndvi}", "color": "#00f3ff"}
            ],
            "description": "NDVI quantifies vegetation health by measuring chlorophyll reflectance. Green indicates thriving crops/forests.",
            "chart_data": {
                "type": "doughnut",
                "labels": ["Dense Vegetation (>30%)", "Moderate Vegetation (8-30%)", "Barren / Non-Veg (<8%)"],
                "data": [high_veg_pct, mod_veg_pct, barren_pct],
                "colors": ["#00ff88", "#ffee00", "#ff4d4d"]
            }
        }

    def run_flood_detection(self, input_image_path, output_image_path):
        img_bgr = cv2.imread(input_image_path)
        if img_bgr is None:
            raise ValueError("Could not read image for Flood Detection.")

        # ── Step 1: Detect Flood / Water Mask ────────────────────────────
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

        lower_water1 = np.array([85, 40, 20])
        upper_water1 = np.array([135, 255, 220])
        mask1 = cv2.inRange(hsv, lower_water1, upper_water1)

        b, g, r = cv2.split(img_bgr.astype(np.float32))
        turbid_water_mask = (b > (r + 15)) & (b > (g - 10)) & (b < 180) & (r < 140)
        mask2 = turbid_water_mask.astype(np.uint8) * 255

        water_mask = cv2.bitwise_or(mask1, mask2)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        water_mask = cv2.morphologyEx(water_mask, cv2.MORPH_OPEN, kernel)
        water_mask = cv2.morphologyEx(water_mask, cv2.MORPH_CLOSE, kernel)

        # ── Step 2: Detect Buildings via Canny + Contours ────────────────
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 40, 120)
        dilated_edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=2)
        bldg_contours, _ = cv2.findContours(dilated_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # ── Step 3: Build the Rescue Priority Overlay ────────────────────
        overlay = img_bgr.copy()

        # Draw translucent flood water in cyan/blue
        flood_color_overlay = img_bgr.copy()
        flood_color_overlay[water_mask > 0] = [220, 180, 0]   # gold/amber water
        blended = cv2.addWeighted(img_bgr, 0.45, flood_color_overlay, 0.55, 0)

        # Draw flood contour boundaries
        flood_contours, _ = cv2.findContours(water_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(blended, flood_contours, -1, (0, 230, 255), 2)

        rescue_count = 0
        safe_count = 0
        PROXIMITY_PX = 25  # pixels to expand building bbox to check for surrounding water

        for c in bldg_contours:
            area = cv2.contourArea(c)
            if area < 80 or area > 18000:
                continue
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.04 * peri, True)
            x, y, w, h = cv2.boundingRect(c)
            aspect = float(w) / max(h, 1)
            if not (0.2 <= aspect <= 5.0):
                continue

            # Expand bounding box to sense surrounding flood water
            x1 = max(0, x - PROXIMITY_PX)
            y1 = max(0, y - PROXIMITY_PX)
            x2 = min(img_bgr.shape[1], x + w + PROXIMITY_PX)
            y2 = min(img_bgr.shape[0], y + h + PROXIMITY_PX)

            zone_mask = water_mask[y1:y2, x1:x2]
            water_in_zone = np.sum(zone_mask > 0)
            zone_area = (x2 - x1) * (y2 - y1)
            water_ratio = water_in_zone / max(zone_area, 1)

            if water_ratio > 0.08:
                # RESCUE REQUIRED — building is in/near flood water
                rescue_count += 1
                cv2.rectangle(blended, (x, y), (x + w, y + h), (0, 0, 255), 2)  # Red box
                cv2.rectangle(blended, (x, y - 20), (x + w, y), (0, 0, 200), -1)  # Label bg
                cv2.putText(blended, "RESCUE!", (x + 3, y - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
            else:
                # Safe structure
                safe_count += 1
                cv2.rectangle(blended, (x, y), (x + w, y + h), (0, 200, 0), 1)  # Green box

        # ── Step 4: Stats & Output ────────────────────────────────────────
        total_pixels = water_mask.size
        water_pixels = int(np.sum(water_mask > 0))
        water_pct = round((water_pixels / total_pixels) * 100, 1)
        inundated_zones_count = len([c for c in flood_contours if cv2.contourArea(c) > 50])

        if water_pct > 25.0 or rescue_count > 5:
            risk_level = "HIGH FLOOD RISK"
            risk_color = "#ff4d4d"
        elif water_pct > 10.0 or rescue_count > 0:
            risk_level = "MODERATE RISK"
            risk_color = "#ffee00"
        else:
            risk_level = "LOW / NORMAL"
            risk_color = "#00ff88"

        output_img = self._add_overlay_legend(blended, [
            ("Flood / Water Zone (Amber)", (0, 200, 255)),
            ("RESCUE REQUIRED Building (Red)", (0, 0, 220)),
            ("Safe Structure (Green)", (0, 200, 0)),
            ("Flood Boundary Contour (Cyan)", (0, 230, 255))
        ], "FLOOD RESCUE PRIORITY MAP")

        cv2.imwrite(output_image_path, output_img)

        return {
            "module": "flood",
            "title": "Flood Detection & Rescue Priority Map",
            "stats": [
                {"label": "Water Surface Coverage", "value": f"{water_pct}%", "color": "#00f3ff"},
                {"label": "Buildings Requiring Rescue", "value": f"{rescue_count} units", "color": "#ff4d4d"},
                {"label": "Safe Structures", "value": f"{safe_count} units", "color": "#00ff88"},
                {"label": "Flood Threat Level", "value": risk_level, "color": risk_color}
            ],
            "description": "Detects flooded zones AND identifies buildings within flood water — flagging them as active RESCUE REQUIRED zones for emergency response teams.",
            "chart_data": {
                "type": "doughnut",
                "labels": ["Water / Flooded Area", "Dry Land"],
                "data": [water_pct, round(100 - water_pct, 1)],
                "colors": ["#00f3ff", "#334155"]
            }
        }

    def run_building_detection(self, input_image_path, output_image_path):
        img_bgr = cv2.imread(input_image_path)
        if img_bgr is None:
            raise ValueError("Could not read image for Building Detection.")

        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        gray_blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(gray_blurred, 50, 150)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        overlay = img_bgr.copy()
        building_count = 0
        built_up_pixels = 0
        small_bldg = 0
        medium_bldg = 0
        large_bldg = 0

        for c in contours:
            area = cv2.contourArea(c)
            if 60 < area < 15000:
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.04 * peri, True)
                x, y, w, h = cv2.boundingRect(c)
                aspect_ratio = float(w) / h
                
                if 0.25 <= aspect_ratio <= 4.0:
                    building_count += 1
                    built_up_pixels += area
                    cv2.drawContours(overlay, [c], -1, (0, 165, 255), 2)
                    cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 255, 255), 1)
                    if area <= 500:
                        small_bldg += 1
                    elif area <= 3000:
                        medium_bldg += 1
                    else:
                        large_bldg += 1

        total_pixels = gray.size
        density_pct = round((built_up_pixels / total_pixels) * 100, 1)

        blended = cv2.addWeighted(img_bgr, 0.4, overlay, 0.6, 0)
        
        output_img = self._add_overlay_legend(blended, [
            ("Building Contour", (0, 165, 255)),
            ("Bounding Rectangle", (0, 255, 255))
        ], "🏠 URBAN BUILDING & INFRASTRUCTURE MAP")

        cv2.imwrite(output_image_path, output_img)

        return {
            "module": "building",
            "title": "Building & Urban Infrastructure Detection",
            "stats": [
                {"label": "Total Detected Structures", "value": f"{building_count} units", "color": "#ff9900"},
                {"label": "Urban Footprint Density", "value": f"{density_pct}%", "color": "#00f3ff"},
                {"label": "Small Structures (<500px2)", "value": f"{small_bldg}", "color": "#00ff88"},
                {"label": "Medium / Large Structures", "value": f"{medium_bldg + large_bldg}", "color": "#e056fd"}
            ],
            "description": "Identifies built-up structures, roofs, and urban footprints to assist city planners and disaster loss assessment.",
            "chart_data": {
                "type": "bar",
                "labels": ["Small (<500px2)", "Medium (500-3k)", "Large (>3k)"],
                "data": [small_bldg, medium_bldg, large_bldg],
                "colors": ["#00ff88", "#ff9900", "#e056fd"]
            }
        }

    def run_land_cover(self, input_image_path, output_image_path):
        img_bgr = cv2.imread(input_image_path)
        if img_bgr is None:
            raise ValueError("Could not read image for Land Cover Classification.")

        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        total_pixels = h.size

        veg_mask = cv2.inRange(hsv, np.array([30, 40, 40]), np.array([90, 255, 255]))
        
        water_mask1 = cv2.inRange(hsv, np.array([95, 50, 30]), np.array([140, 255, 240]))
        b, g, r = cv2.split(img_bgr.astype(np.float32))
        water_mask2 = ((b > (r + 15)) & (b > (g - 10)) & (v < 180)).astype(np.uint8) * 255
        water_mask = cv2.bitwise_or(water_mask1, water_mask2)
        water_mask[veg_mask > 0] = 0

        soil_mask = cv2.inRange(hsv, np.array([10, 35, 80]), np.array([30, 220, 255]))
        soil_mask[veg_mask > 0] = 0
        soil_mask[water_mask > 0] = 0

        urban_mask = np.ones_like(h, dtype=np.uint8) * 255
        urban_mask[veg_mask > 0] = 0
        urban_mask[water_mask > 0] = 0
        urban_mask[soil_mask > 0] = 0

        veg_pct = round((np.sum(veg_mask > 0) / total_pixels) * 100, 1)
        water_pct = round((np.sum(water_mask > 0) / total_pixels) * 100, 1)
        soil_pct = round((np.sum(soil_mask > 0) / total_pixels) * 100, 1)
        urban_pct = round((np.sum(urban_mask > 0) / total_pixels) * 100, 1)

        classified_map = np.zeros_like(img_bgr)
        classified_map[veg_mask > 0] = [34, 139, 34]
        classified_map[water_mask > 0] = [238, 104, 0]
        classified_map[soil_mask > 0] = [71, 192, 255]
        classified_map[urban_mask > 0] = [128, 0, 128]

        blended = cv2.addWeighted(img_bgr, 0.35, classified_map, 0.65, 0)

        output_img = self._add_overlay_legend(blended, [
            (f"Vegetation ({veg_pct}%)", (34, 139, 34)),
            (f"Water Bodies ({water_pct}%)", (238, 104, 0)),
            (f"Bare Soil ({soil_pct}%)", (71, 192, 255)),
            (f"Urban / Roads ({urban_pct}%)", (128, 0, 128))
        ], "🗺️ LAND COVER THEMATIC CLASSIFICATION")

        cv2.imwrite(output_image_path, output_img)

        return {
            "module": "landcover",
            "title": "Land Cover Classification",
            "stats": [
                {"label": "Forest & Crops", "value": f"{veg_pct}%", "color": "#00ff88"},
                {"label": "Water Resources", "value": f"{water_pct}%", "color": "#00f3ff"},
                {"label": "Bare Soil / Fallow", "value": f"{soil_pct}%", "color": "#ffee00"},
                {"label": "Urban & Built-Up", "value": f"{urban_pct}%", "color": "#e056fd"}
            ],
            "description": "Categorizes satellite imagery into environmental classes for land-use monitoring and climate tracking.",
            "chart_data": {
                "type": "pie",
                "labels": ["Vegetation / Forest", "Water Bodies", "Bare Soil", "Urban / Roads"],
                "data": [veg_pct, water_pct, soil_pct, urban_pct],
                "colors": ["#00ff88", "#00f3ff", "#ffee00", "#e056fd"]
            }
        }

    def _add_overlay_legend(self, img, items, header_title):
        h, w = img.shape[:2]
        
        # Dynamic scaling factor based on image resolution
        scale = min(w, h) / 750.0
        scale = max(0.42, min(0.9, scale))  # Scale nicely between 0.42 and 0.9

        font_scale_title = 0.5 * scale
        font_scale_item = 0.42 * scale
        thickness = max(1, int(1 * scale))
        title_thickness = max(1, int(2 * scale))

        box_w = int(min(310 * scale, w * 0.42))
        item_h = int(22 * scale)
        box_h = int(30 * scale + len(items) * item_h)
        
        margin = max(6, int(10 * scale))
        
        overlay = img.copy()
        cv2.rectangle(overlay, (margin, margin), (margin + box_w, margin + box_h), (15, 15, 25), -1)
        cv2.rectangle(overlay, (margin, margin), (margin + box_w, margin + box_h), (0, 243, 255), thickness)

        # Soft 60% opacity background so ground features under the legend are still visible
        cv2.addWeighted(overlay, 0.65, img, 0.35, 0, img)

        title_y = margin + int(18 * scale)
        cv2.putText(img, header_title, (margin + int(8 * scale), title_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale_title, (0, 243, 255), title_thickness, cv2.LINE_AA)

        y = title_y + int(20 * scale)
        color_box_size = int(12 * scale)
        
        for label, color in items:
            box_x1 = margin + int(8 * scale)
            box_y1 = y - color_box_size
            box_x2 = box_x1 + color_box_size
            box_y2 = y
            
            cv2.rectangle(img, (box_x1, box_y1), (box_x2, box_y2), color, -1)
            cv2.rectangle(img, (box_x1, box_y1), (box_x2, box_y2), (255, 255, 255), 1)
            
            cv2.putText(img, label, (box_x2 + int(6 * scale), y - int(2 * scale)), 
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale_item, (240, 240, 240), thickness, cv2.LINE_AA)
            y += item_h

        return img
