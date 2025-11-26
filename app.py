@app.route('/api_docs')
def api_docs():
    """Render API documentation page"""
    return render_template('api_docs.html')
