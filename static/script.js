function validateFile() {
    const fileInput = document.getElementById('file');
    const filePath = fileInput.value;
    const allowedExtensions = /(\.jpg|\.jpeg|\.png)$/i;

    if (!allowedExtensions.exec(filePath)) {
        // Muestra el modal en lugar de alert
        const fileErrorModal = new bootstrap.Modal(document.getElementById('fileErrorModal'));
        fileErrorModal.show();
        fileInput.value = ''; // Limpiar el campo de archivo
        return false;
    }
    return true;
}
