'''
Created on Jan 18, 2017

@author: Greg Petrochenkov
'''

from Web.flow_calc import FlowCalculator
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
import os
from StringIO import StringIO
from PIL import Image
import pandas as pd


app = Flask(__name__)
#UPLOAD_FOLDER = '/opt/django/webapps/pubs_ui/FloodAnalysis/FloodAnalysis27/Web/uploads'
UPLOAD_FOLDER = 'C:\\Users\\chogg\\Documents\\GitHub\\FloodAnalysis_v2\\FloodAnalysis27\\Web\\uploads'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'csv'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS

flow_calculator = FlowCalculator()

@app.route('/')
def render_layout():
    '''
    Main layout for application
    '''
    
    return render_template("layout.html")

@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('static/js', path)

@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory('static/css', path)

@app.route('/images/<path:path>')
def send_images(path):
    return send_from_directory('static/images', path)

@app.route('/query_nwis', methods=['POST'])
def query_nwis():
    '''
    Queries NWIS given the form parmeters
    '''
    
    station_id = request.form['station_id']
    start_date = str(request.form['start_date'])
    end_date = str(request.form['end_date'])
    tz = request.form['tz']
    ds = request.form['daylight_savings']

    flow_calculator.get_nwis_ts(station_id, start_date, end_date, tz, ds)
    d = {"message": "Queried NWIS station %s" % station_id}
    
    return jsonify(**d)

@app.route('/calculate_geometry', methods=['POST'])
def calculate_geometry():
    '''
    Calculates Cross-sectional Geometry and Reads or Computes
    Hydraulic Properties Table
    '''
    
    #cross section geometry file
    coord_file = request.files["coord_file"]
    flow_calculator.coord_file = os.path.join(app.config['UPLOAD_FOLDER'], 
                 secure_filename(coord_file.filename))
    coord_file.save(flow_calculator.coord_file)
    
    #datum for stage
    flow_calculator.datum = float(request.form["datum"])
    
    #subdivisions
    flow_calculator.sub_divisions = \
    [int(y) for y in [x for x in
                     request.form['sub_divisions'].split(',') 
                     if x != '']]
    
    #auto calculation of table or read from file
    flow_calculator.auto = str(request.form["auto_calculate"])
    if flow_calculator.auto == "false":
        properties_file = request.files["properties_file"]
        flow_calculator.properties_file = os.path.join(app.config['UPLOAD_FOLDER'], 
                                secure_filename(properties_file.filename))
        properties_file.save(flow_calculator.properties_file)
    else:
        flow_calculator.stage_increment = request.form["z_step"]
       
    flow_calculator.create_table()
    
    d = {"message": "Table is setup and ready to process/download",
         "graph": flow_calculator.cross_section_graph}
    
    return jsonify(**d)

@app.route('/flood_parameters', methods=['POST'])
def flood_parameters():
    '''
    Assigns values to flood parameters
    '''
    
    #Known flood conditions 
    flow_calculator.channel_bed_slope = float(request.form["channel_bed_slope"])
    flow_calculator.stage_hB = float(request.form["stage_hB"])
    flow_calculator.stage_hp = float(request.form["stage_hp"])
    flow_calculator.rise_peak_delta = float(request.form["days_between"])
    flow_calculator.flow_QB = float(request.form["flow_QB"])
    flow_calculator.flow_Qp = float(request.form["flow_Qp"])
    flow_calculator.flow_Q0 = float(request.form["flow_Q0"])
    
    d = {"message": "Flood parameters are now set up",
         "graph": flow_calculator.cross_section_graph}
    
    return jsonify(**d)

@app.route('/newton_raphson', methods=['POST'])
def newton_raphson():
    '''
    Reads in table manning's n vs. stage or static manning's n,
    computes Q via the Newton Raphson Method and finally outputs
    the graphs for the results
    '''
    
    #methods regarding manning's n, either static for all stage
    #or reads in a table of stage vs. manning's n
    flow_calculator.static_manning = str(request.form["static_calculate"])
    
    if flow_calculator.static_manning == 'true':
        #manning coefficient
        flow_calculator.manning_rough = float(request.form["manning_coef"])
    else:
        manning_file = request.files["manning_file"]
        flow_calculator.manning_file = os.path.join(app.config['UPLOAD_FOLDER'], 
                                secure_filename(manning_file.filename))
        manning_file.save(flow_calculator.manning_file)
        
        flow_calculator.manning_df = pd.read_csv(flow_calculator.manning_file)
        flow_calculator.manning_df.columns = [["Stage", "n"]]
        
    #Initialize the time series data and then process via the Newton Raphson method
    flow_calculator.initialize_timeseries_data_for_newton_method()
    flow_calculator.flow_newton_raphson_method()
    
    #if discrete and/or alt output, include the
    #discrete flow field measurements and/or the 
    #alternative approximated flow
    
    if str(request.form["discrete_output"]) == "true":
        flow_calculator.graph_output.discrete_discharge = True
    else:
        flow_calculator.graph_output.discrete_discharge = False
        
    if str(request.form["alt_output"]) == "true":
        flow_calculator.graph_output.alt_discharge = True
    else:
        flow_calculator.graph_output.alt_discharge = False
        
    flow_calculator.process_results()
    
    d = {"message": "Table is setup and ready to process/download",
         "ssr": flow_calculator.SSR}
    
    return jsonify(**d)
    
@app.route('/download_table', methods=['GET','POST'])
def download_table():
    '''
    Downloads the hydraulic properties table
    '''
    
    file_name = os.path.join(app.config['UPLOAD_FOLDER'], 
                secure_filename("table.csv"))
                
    flow_calculator.properties_df.to_csv(path_or_buf=file_name)
    
    return send_file(file_name, mimetype="text/csv",
                     as_attachment = True,
                 attachment_filename = "table.csv")
    
@app.route('/download_flow_table', methods=['GET','POST'])
def download_flow_table():
    '''
    Downloads the time series of stage and flow table
    '''
    
    file_name = os.path.join(app.config['UPLOAD_FOLDER'], 
                secure_filename("flow_table.csv"))
                
    flow_calculator.flow_df.to_csv(path_or_buf=file_name)
    
    return send_file(file_name, mimetype="text/csv",
                     as_attachment = True,
                 attachment_filename = "flow_table.csv")
                 
@app.route('/image')
def serve_img():
    '''
    Serves an image to the client
    '''
    
    name = request.args.get('name')
    file_name = ''.join([UPLOAD_FOLDER,'/',name,'.png'])
    img = Image.open(file_name)
    return serve_pil_image(img)

def serve_pil_image(pil_img):
    '''
    Puts the image data in a string buffer and then returns the data
    to serve the image to the client
    '''
    
    img_io = StringIO()
    pil_img.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg')  
    
app.secret_key = os.urandom(24)
app.run()
