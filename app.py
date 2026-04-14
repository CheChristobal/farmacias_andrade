from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename # Para manejar nombres de archivos seguros
import os

app = Flask(__name__)

# --- CONFIGURACIÓN DE SEGURIDAD Y ARCHIVOS ---
app.secret_key = 'clave_super_secreta_andrade'
ADMIN_PASSWORD = 'Andrade2026'

# Configuración de subida de imágenes
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Si no existe la carpeta de subidas, la creamos
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Configuración de la Base de Datos
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'farmacia.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Función para validar extensiones de imagen
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- MODELO ---
class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Integer, nullable=False)
    categoria = db.Column(db.String(50), default="General")
    imagen = db.Column(db.String(200), default="default.jpg") # Nuevo campo para la ruta

with app.app_context():
    db.create_all()

# --- RUTAS ---

@app.route('/')
def inicio():
    return render_template('inicio.html')

@app.route('/catalogo')
def catalogo():
    categoria = request.args.get('categoria')
    busqueda = request.args.get('q')
    
    query = Producto.query

    if categoria:
        query = query.filter_by(categoria=categoria)
    
    if busqueda:
        query = query.filter(Producto.nombre.contains(busqueda))

    productos = query.all()
    return render_template('catalogo.html', productos=productos)

@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            flash('Contraseña incorrecta. Inténtalo de nuevo.')
    return render_template('login.html')

@app.route('/admin/panel', methods=['GET', 'POST'])
def admin_panel():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        nuevo_nombre = request.form.get('nombre')
        nuevo_precio = request.form.get('precio')
        nueva_cat = request.form.get('categoria')
        file = request.files.get('imagen') # Capturamos el archivo

        # Manejo de la imagen
        filename = "default.jpg"
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        nuevo_prod = Producto(
            nombre=nuevo_nombre, 
            precio=int(nuevo_precio), 
            categoria=nueva_cat,
            imagen=filename
        )
        db.session.add(nuevo_prod)
        db.session.commit()
        flash('Producto agregado con éxito')
        return redirect(url_for('admin_panel'))

    productos = Producto.query.all()
    return render_template('admin.html', productos=productos)

@app.route('/admin/eliminar/<int:id>')
def eliminar(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    producto = Producto.query.get(id)
    if producto:
        # Opcional: Borrar el archivo físico si no es el default
        if producto.imagen != "default.jpg":
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], producto.imagen))
            except:
                pass
        
        db.session.delete(producto)
        db.session.commit()
        flash('Producto eliminado')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('inicio'))

@app.route('/contacto')
def contacto():
    return render_template('contacto.html')

@app.route('/producto/<int:id>')
def detalle_producto(id):
    producto = Producto.query.get_or_404(id)
    # Sugerencia: buscar productos relacionados de la misma categoría
    relacionados = Producto.query.filter(Producto.categoria == producto.categoria, Producto.id != id).limit(4).all()
    return render_template('detalle.html', producto=producto, relacionados=relacionados)

if __name__ == '__main__':
    app.run(debug=True)