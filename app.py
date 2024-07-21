from flask import Flask, render_template, request
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from PIL import Image, UnidentifiedImageError
import os

app = Flask(__name__)

# Cargar el modelo
MODEL_PATH = 'mi_modelo.h5'
model = load_model(MODEL_PATH)

# Definir el umbral de confianza
CONFIDENCE_THRESHOLD = 0.95

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        # Obtener el archivo de la solicitud
        file = request.files['file']
        
        # Verificar la extensión del archivo
        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS):
            return render_template('index.html', prediction="Formato de archivo no soportado. Solo se permiten archivos PNG o JPG.")

        # Guardar el archivo en una carpeta temporal
        basepath = os.path.dirname(__file__)
        file_path = os.path.join(basepath, 'uploads', file.filename)
        file.save(file_path)
        
        try:
            # Preprocesar la imagen para el modelo
            img = image.load_img(file_path, target_size=(50, 50))  # Ajustar el tamaño según el modelo
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)  # Añadir una dimensión para el batch
            img_array = img_array / 255.0  # Normalizar los valores de los píxeles
            
            # Hacer una predicción
            prediction = model.predict(img_array)
            confidence = np.max(prediction)  # Obtener la confianza de la predicción
            result = np.argmax(prediction, axis=1)[0]  # Obtener la clase predicha
            
            # Mapear la clase predicha a una etiqueta de enfermedad
            labels = {0: 'Black Rot', 1: 'ESCA', 2: 'Healthy', 3: 'Leaf Blight'}  # Ajustar según las etiquetas de tu modelo
            
            if confidence >= CONFIDENCE_THRESHOLD and result in labels:
                prediction_label = labels[result]
            else:
                prediction_label = "Etiqueta desconocida o baja confianza"
        
        except UnidentifiedImageError:
            return render_template('index.html', prediction="Error al identificar el archivo de imagen.")
        
        return render_template('index.html', prediction=prediction_label)
    return None

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 3100)))
