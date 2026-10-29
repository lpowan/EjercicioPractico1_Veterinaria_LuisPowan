document.addEventListener('DOMContentLoaded', () => {

    // Muestra los avisos (toast) enviados con RedirectAttributes
    document.querySelectorAll('.toast').forEach((aviso) => {
        bootstrap.Toast.getOrCreateInstance(aviso).show();
    });

    // Pasa el id y el nombre del registro al modal de confirmacion
    const ventanaConfirmacion = document.getElementById('ventanaConfirmacion');
    if (ventanaConfirmacion) {
        ventanaConfirmacion.addEventListener('show.bs.modal', (evento) => {
            const botonEliminar = evento.relatedTarget;
            document.getElementById('registroId').value = botonEliminar.dataset.id;
            document.getElementById('registroNombre').textContent = botonEliminar.dataset.nombre;
        });
    }
});
