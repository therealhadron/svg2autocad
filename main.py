import array
import re
import comtypes.client
from bs4 import BeautifulSoup

# Get running instance of the AutoCAD application
acad = comtypes.client.GetActiveObject("AutoCAD.Application")

# Document object
doc = acad.ActiveDocument

# Get the ModelSpace object
ms = doc.ModelSpace
ACTIONS = {"M", "m", "l", "c"}
SVG_PATH = "./frames/image2380.svg" # Path of SVG file here

data = open(SVG_PATH, "r")
soup = BeautifulSoup(data, 'xml')
soup = soup.find_all('path')
soup = str(soup)
soup = soup.replace('<path d="',"")
soup = soup.replace('"/>',"")
svg_data = re.finditer(r'([a-zA-Z]|-?[0-9]+)', soup)

working_array = []
# Start coords for the beginnning of a path for the end point (z) to return to at the end of a path
current_coord_x = current_coord_y = startCoordX = startCoordY = 0
tag = ""

def create_spline(spline_points):
    global current_coord_x, current_coord_y
    start_tan = end_tan = array.array ('d', [0,0,0])
    previous_x = current_coord_x
    previous_y = current_coord_y
    # For setting up the intial spline start and end point
    spline_arr = array.array ('d', [])
    # For creating smoother curves
    spline_srt = array.array ('d', [])
    spline_end = array.array ('d', [])

    # For initial spline coord AND for control point smoothing
    for i in range(0, len(spline_points), 6):
        a, b, c, d, e, f = spline_points[i:i+6]
        spline_srt.extend((a + previous_x, b + previous_y, 0))
        spline_end.extend((c + previous_x, d + previous_y, 0))
        spline_arr.extend((previous_x, previous_y, 0, e + previous_x, f + previous_y, 0))
        previous_x = spline_arr[3]
        previous_y = spline_arr[4]
        
        line = ms.addspline(spline_arr, start_tan, end_tan) # Draws initial spline
        line.setControlPoint(1, spline_srt)
        line.setControlPoint(2, spline_end)
        # Reset points
        spline_arr = array.array ('d', [])
        spline_srt = array.array ('d', [])
        spline_end = array.array ('d', [])

    # Updates the global cursor coordinates
    current_coord_x = previous_x
    current_coord_y = previous_y

# Draw a line from current cursor coordinates
def create_line(linePoints):
    global current_coord_x, current_coord_y
    current_p1 = array.array('d', [])
    current_p2 = array.array('d', [])

    for i in range(0, len(linePoints), 2):
        x, y = linePoints[i:i+2]
        current_p1.extend((current_coord_x, current_coord_y, 0))
        current_p2.extend((x + current_coord_x, y + current_coord_y, 0))
        current_coord_x += x
        current_coord_y += y
        line = ms.addLine(current_p1,current_p2)
        # Reset points
        current_p1 = array.array('d', [])
        current_p2 = array.array('d', [])

# Moves cursor relative from current coordinates
def move_point(move_points):
    global current_coord_x, current_coord_y
    current_coord_x += move_points[0]
    current_coord_y += move_points[1]

#Picks up pen move it to the specified coordinates
def start_point(start_points):
    global current_coord_x, current_coord_y
    current_coord_x = start_points[0]
    current_coord_y = start_points[1]

def tag_check(tag, working_array):
    if tag == "l":
        create_line(working_array)
    elif tag == "c":
        create_spline(working_array)
    elif tag == "m":
        move_point(working_array)
    elif tag == "M":
        start_point(working_array)

for element in svg_data:
    if element.group(0) in ACTIONS:
        tag_check(tag, working_array)
        working_array = []
        tag = str(element.group(0))
        continue
    elif element.group(0) == "z":
        continue
    working_array.append(int(element.group(0)))