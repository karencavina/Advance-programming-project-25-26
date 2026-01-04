from flask import Flask, render_template, request, redirect, url_for, send_from_directory, abort, flash
from werkzeug.utils import secure_filename 
from werkzeug.exceptions import RequestEntityTooLarge
import os
# from part 1 we need to import some functions
from graph import OntologyGraph, GONode, GOEdge

STATE = {
    "loaded": False,
    "obo": None,
    "gaf": None,
    "graph": None
}


# Temporary function to build a demo graph
def build_demo_graph():
    """Temporary graph so Part 4 works without Part 1."""
    g = OntologyGraph()

    a = GONode("GO:0008150", "biological_process",
               "biological_process", "root BP")
    b = GONode("GO:0009987", "cellular process",
               "biological_process", "child")
    c = GONode("GO:0007049", "cell cycle",
               "biological_process", "child")

    for n in (a, b, c):
        g.new_node(n)

    g.new_edge(a, GOEdge(a, b, "is_a"))
    g.new_edge(b, GOEdge(b, c, "is_a"))
    return g



# flask set up 
app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for flash messages
# paths / folders 
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 40 MB limit
app.config['ALLOWED_EXTENSIONS'] = {'.obo','.gaf','.gaf.gz'}

# Ensure upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

#Routs 
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/upload', methods=['GET','POST'])
def upload():
    if request.method == "GET":
        return render_template("upload.html", state=STATE)

    obo = request.files.get("obo_file")
    gaf = request.files.get("gaf_file")

    if not obo or not gaf:
        flash("Please upload both OBO and GAF files.", "error")
        return redirect(url_for("upload"))

    obo_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(obo.filename))
    gaf_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(gaf.filename))

    obo.save(obo_path)
    gaf.save(gaf_path)

    # Part 1 will replace this later
    STATE["graph"] = build_demo_graph()
    STATE["obo"] = obo_path
    STATE["gaf"] = gaf_path
    STATE["loaded"] = True

    flash("Files uploaded successfully.", "success")
    return redirect(url_for("home"))
        


@app.route('/search')
def search():
    query = request.args.get('query', '')
    # Here you would add logic to search the ontology data store
    results = []  # Placeholder for search results
    return render_template('search.html', query=query, results=results)

@app.route('/visualize')
def visualize():
    return render_template('visualize.html')

if __name__== '__main__': 
    app.run(debug=True)


    

