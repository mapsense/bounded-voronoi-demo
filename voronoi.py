import json
import csv
from shapely.geometry import LineString, Polygon, Point, box
from shapely.ops import polygonize
from scipy.spatial import Voronoi

def make_bounded_voronoi(point_id_tuples, boundary):
    #################
    # Boundary: polygon object
    # Point_id_tuples: ((lon, lat), id)
    # Returns geojson
    ################
    # Get bbox 
    bbox = boundary.boundary.bounds
    # Find maximum dimension of bbox
    min_distance = max(bbox[2]-bbox[0], bbox[3]-bbox[1])
    # Double it for safety
    safety_margin = min_distance * 2
    # Get points at corners of buffered bbox
    fake_points = box(bbox[0] - safety_margin, 
                  bbox[1] - safety_margin, 
                  bbox[2] + safety_margin,
                  bbox[3] + safety_margin).exterior.coords[:-1]
    # Make voronoi
    vor = Voronoi([x[0] for x in points] + fake_points)
    features = []
    for region_idx, eye_dee in zip(vor.point_region, [x[1] for x in points]):
        region = vor.regions[region_idx]
        # If region is finite
        if region and -1 not in region:
            coords = []
            # Get coordinates of vertices
            for vertex_idx in region:
                coords.append(vor.vertices[vertex_idx])
            # Make polygon, intersect with boundary object
            poly = Polygon(coords).intersection(boundary)
            # Generate polygon feature
            try:
                feature_dict = {"type": "Feature",
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [poly.exterior.coords[:]]
                                },
                            "properties": {
                                "id": eye_dee
                                }
                            }
            # ...or MultiPolygon
            except AttributeError:
                feature_dict = {"type": "Feature",
                                "geometry": {
                                    "type": "MultiPolygon",
                                    "coordinates": [[x.exterior.coords[:]] for x in poly.geoms]
                                    },
                                "properties": {
                                    "id": eye_dee
                                    }
                                }
            # Add to features list
            features.append(feature_dict)
    return {"type": "FeatureCollection", "features": features}

if __name__ == '__main__':
    # Get outline
    # Load GeoJSON
    us = json.load(open('gz_2010_us_outline_500k.json'))
    # Create LineStrings from GeoJSON
    features = [LineString(feature['geometry']['coordinates']) for feature in us['features']]
    # Create Polygons, select US outline
    us = list(polygonize(features))[0]
    # Get points
    points = []
    with open('example_points.csv') as f:
        for row in csv.reader(f):
            # Read flat file into ((Long, Lat), id) tuples
            data = (float(row[0]), float(row[1])), row[2]
            points.append(data)

# Make geojson
vor_geojson = make_bounded_voronoi(points, us)
# Write to file
with open('voronoi.geojson', 'w') as f:
    json.dump(vor_geojson, f)

