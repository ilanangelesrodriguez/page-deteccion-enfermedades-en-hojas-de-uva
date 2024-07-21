from flask import Flask, render_template, request, redirect, url_for
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from PIL import Image
import os

app = Flask(__name__)

# Cargar el modelo
MODEL_PATH = 'mi_modelo.h5'
model = load_model(MODEL_PATH)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        # Obtener el archivo de la solicitud
        file = request.files['file']

        # Guardar el archivo en una carpeta temporal
        basepath = os.path.dirname(__file__)
        file_path = os.path.join(basepath, 'uploads', file.filename)
        file.save(file_path)

        # Preprocesar la imagen para el modelo
        img = image.load_img(file_path, target_size=(224, 224))  # Ajustar el tamaño según el modelo
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)  # Añadir una dimensión para el batch

        # Hacer una predicción
        prediction = model.predict(img_array)
        result = np.argmax(prediction, axis=1)[0]  # Obtener la clase predicha

        # Mapear la clase predicha a una etiqueta de enfermedad
        labels = {0: 'Black Rot', 1: 'ESCA', 2: 'Healthy', 3: 'Leaf Blight'}  # Ajustar según las etiquetas de tu modelo
        if result in labels:
            prediction_label = labels[result]
        else:
            prediction_label = "Etiqueta desconocida"

        # Detalles adicionales de la predicción
        prediction_confidence = np.max(prediction)  # Confianza de la predicción
        prediction_probabilities = prediction[0]  # Probabilidades de todas las clases



        return render_template('index.html', prediction=prediction_label, 
                                confidence=prediction_confidence,
                                probabilities=prediction_probabilities.tolist())
    return None


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 2100)))