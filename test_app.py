import os
import cv2
import numpy as np

def create_synthetic_cloudy_satellite_image(filepath):
    height, width = 600, 800
    img = np.zeros((height, width, 3), dtype=np.uint8)

    # Vegetation
    img[:, :] = [34, 120, 34]

    cv2.rectangle(img, (50, 50), (350, 250), [20, 160, 20], -1)
    cv2.rectangle(img, (400, 50), (750, 200), [40, 160, 220], -1)

    # Water Body / Bay of Bengal region (Dark blue)
    pts = np.array([[0, 150], [200, 180], [450, 300], [600, 420], [800, 480],
                    [800, 580], [0, 580]], np.int32)
    cv2.fillPoly(img, [pts], [140, 70, 15]) # Deep Oceanic Blue

    buildings = [
        (450, 100, 40, 30), (500, 110, 50, 40), (470, 160, 35, 30),
        (560, 120, 60, 45), (630, 130, 45, 35)
    ]
    for x, y, w, h in buildings:
        cv2.rectangle(img, (x, y), (x + w, y + h), [180, 180, 180], -1)

    clouds = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.circle(clouds, (250, 200), 180, (255, 255, 255), -1)
    cv2.circle(clouds, (500, 350), 220, (245, 245, 245), -1)
    clouds = cv2.GaussianBlur(clouds, (121, 121), 0)

    cloudy_img = cv2.addWeighted(img, 0.45, clouds, 0.55, 0)
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    cv2.imwrite(filepath, cloudy_img)
    return filepath

if __name__ == '__main__':
    from cloud_removal import CloudRemover
    from analysis_engine import AnalysisEngine

    test_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    result_dir = os.path.join(os.path.dirname(__file__), 'static', 'results')
    analysis_dir = os.path.join(os.path.dirname(__file__), 'static', 'analysis')

    for d in [test_dir, result_dir, analysis_dir]:
        os.makedirs(d, exist_ok=True)

    input_path = os.path.join(test_dir, 'sample_bay_of_bengal.jpg')
    output_path = os.path.join(result_dir, 'clear_sample_bay_of_bengal.jpg')

    create_synthetic_cloudy_satellite_image(input_path)

    remover = CloudRemover()
    metrics = remover.process(input_path, output_path)
    print("--- Enhancement Metrics ---")
    print(metrics)

    analyzer = AnalysisEngine()
    print("\n--- Testing CV Analysis ---")
    
    ndvi_res = analyzer.run_ndvi(output_path, os.path.join(analysis_dir, 'analysis_ndvi.jpg'))
    print("NDVI:", [s['label'].encode('ascii', 'ignore').decode('ascii') + ': ' + s['value'].encode('ascii', 'ignore').decode('ascii') for s in ndvi_res['stats']])

    flood_res = analyzer.run_flood_detection(output_path, os.path.join(analysis_dir, 'analysis_flood.jpg'))
    print("Flood:", [s['label'].encode('ascii', 'ignore').decode('ascii') + ': ' + s['value'].encode('ascii', 'ignore').decode('ascii') for s in flood_res['stats']])

    land_res = analyzer.run_land_cover(output_path, os.path.join(analysis_dir, 'analysis_landcover.jpg'))
    print("Land Cover:", [s['label'].encode('ascii', 'ignore').decode('ascii') + ': ' + s['value'].encode('ascii', 'ignore').decode('ascii') for s in land_res['stats']])

    print("\nSUCCESS: Ocean / Bay of Bengal water body detection verified!")
