from flask import Flask, render_template, request, redirect, url_for, send_from_directory, abort, flash
from werkzeug.utils import secure_filename 
from werkzeug.exceptions import RequestEntityTooLarge
import os
import module1
import module3
from graph import *

STATE = {
    "loaded": False,
    "obo": None,
    "gaf": None,
    "graph": None,
    'data': None,
    'analysis': None
}

# flask set up 
app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for flash messages

# paths / folders 
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 400 * 1024 * 1024  # 400 MB limit
app.config['ALLOWED_EXTENSIONS'] = {'.obo','.gaf','.gaf.gz'}

def allowed_file(filename):
    if not filename:
        return False
    else:
        name=  filename.lower()
    return name.endswith(".obo") or name.endswith(".gaf") or name.endswith(".gaf.gz")

# Ensure upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


# handle file size limit error
@app.errorhandler(RequestEntityTooLarge)
def handle_file_size_error(e):
    flash("File is too large. Maximum allowed size is 200 MB.", "error")
    return redirect(url_for("upload"))



#Routs 
@app.route('/')
def home():
    return render_template('home.html', state=STATE)


@app.route('/upload', methods=['GET','POST'])
def upload():
    if request.method == "GET":
        return render_template("upload.html", state=STATE)

    obo = request.files.get("obo_file")
    gaf = request.files.get("gaf_file")

    if not obo or not gaf or obo.filename == "" or gaf.filename == "":
        flash("Please upload both OBO and GAF files.", "error")
        return redirect(url_for("upload"))
    if not allowed_file(obo.filename):
        flash("Invalid OBO file type. Please upload a .obo file.", "error")
        return redirect(url_for("upload"))
    if not allowed_file(gaf.filename):
        flash("Invalid GAF file type. Please upload a .gaf or .gaf.gz file.", "error")
        return redirect(url_for("upload"))

    obo_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(obo.filename))
    gaf_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(gaf.filename))

    obo.save(obo_path)
    gaf.save(gaf_path)
    try:
        data = module1.load_all(obo_path, gaf_path)
        graph = create_graph(data)
        analysis = module3.Analysis(graph)

        STATE["data"] = data
        STATE["graph"] = graph
        STATE["obo"] = obo_path
        STATE["gaf"] = gaf_path
        STATE["loaded"] = True
        STATE["analysis"] = analysis

        flash("Files uploaded successfully.", "success")
        return redirect(url_for("home"))
    
    except Exception as e:
        app.logger.exception("Error while processing uploaded files")
        flash(f"An error occurred while processing the files: {str(e)}", "error")
        return redirect(url_for("upload"))
    


@app.route('/search')
def search():    
    if not STATE["loaded"]:
        flash("Please upload files before searching.", "error")
        return redirect(url_for("upload"))
    
    query = request.args.get("q", "").strip()
    results = []
    if query:
        for node in STATE["graph"].get_GONodes():
            if query.lower() in node.go_id.lower() or query.lower() in node.name.lower():
                results.append(node)
    return render_template('search.html', state=STATE, query=query, results=results,)



@app.route("/term/<go_id>")
def term_detail(go_id):
    if not STATE["loaded"]:
        flash("Please upload files before viewing term details.", "error")
        return redirect(url_for("upload"))
    
    try:
        node = STATE["graph"].get_node(go_id)
    
    except KeyError:
        flash(f"Term with ID {go_id} not found.", "error")
        return redirect(url_for("search"))
    
    parents= STATE["graph"].get_parents(node, edge=False) or []
    children= STATE["graph"].get_children(node, edge=False) or []
    neighbours = STATE["analysis"].get_Neighbours(node) or []
    annotations_df = STATE["analysis"].get_goterm_annotations(go_id)
    annotations =[] if annotations_df is None else annotations_df.to_dict("records")

    return render_template(
        'term_detail.html',
        state=STATE, 
        node=node, 
        parents=parents, 
        children=children,
        neighbours=neighbours,
        annotations=annotations
    )


@app.route('/similarity', methods=['GET','POST'])
def similarity():
    if not STATE["loaded"]:
        flash("Please upload files before calculating similarity.", "error")
        return redirect(url_for("upload"))

    similarity_score = None
    node1 = None
    node2 = None

    if request.method == "POST":
        go_id1 = request.form.get("go_id1", "").strip()
        go_id2 = request.form.get("go_id2", "").strip()

        try:
            node1 = STATE["graph"].get_node(go_id1)
            node2 = STATE["graph"].get_node(go_id2)
            similarity_score = STATE["analysis"].get_Similarity(node1, node2)
            path = STATE["analysis"].path_Finder(node1, node2)

        except KeyError as e:
            flash(str(e), "error")
            return redirect(url_for("similarity"))
        
    return render_template(
        'similarity.html',
        state=STATE,
        similarity=similarity_score,
        node1=node1,
        node2=node2
    )



@app.route("/stats")
def stats():
    if not STATE["loaded"]:
        flash("Please upload files first.", "error")
        return redirect(url_for("upload"))

    #stats_data = STATE["analysis"].get_Statistics()
    #return render_template("stats.html", state=STATE, stats=stats_data)
    return render_template("stats.html", state=STATE, stats=module3.statistics)

if __name__== '__main__': 
    app.run(debug=True)

