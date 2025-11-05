import { useEffect, useState } from "react"
import { FaFileMedical, FaHistory, FaDownload, FaPaperPlane, FaClock, FaCheckCircle, FaTimesCircle, FaHourglassHalf } from "react-icons/fa"

// --- Componente de Badge de Estado ---
function StatusBadge({ estado }) {
    let icon = <FaClock />;
    let className = 'status-badge ';

    switch (estado.toLowerCase()) {
        case 'solicitado':
            icon = <FaPaperPlane />;
            className += 'pending';
            break;
        case 'en revisión':
            icon = <FaHourglassHalf />;
            className += 'review';
            break;
        case 'aprobado':
            icon = <FaCheckCircle />;
            className += 'ok';
            break;
        case 'rechazado':
            icon = <FaTimesCircle />;
            className += 'danger';
            break;
        default:
            className += 'pending';
    }

    return (
        <span className={className}>
            {icon} {estado}
        </span>
    );
}

// --- Componente para la sección "Solicitar Nuevo" ---
function SolicitarTramite({ disponibles, loading, onSolicitar }) {
    const [selectedModule, setSelectedModule] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        // Si la lista de disponibles cambia (ej. después de solicitar),
        // resetea el select al primer item o a vacío.
        if (disponibles && disponibles.length > 0) {
            setSelectedModule(disponibles[0].modulo_id);
        } else {
            setSelectedModule("");
        }
    }, [disponibles]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!selectedModule) return;

        setIsSubmitting(true);
        // Llama a la función 'onSolicitar' pasada como prop
        await onSolicitar(Number(selectedModule));
        setIsSubmitting(false);
    }

    return (
        <section className="tramite-section solicitar-section">
            <h2><FaFileMedical /> Solicitar Nuevo Certificado</h2>
            {loading ? (
                <p>Buscando módulos aprobados disponibles...</p>
            ) : disponibles.length === 0 ? (
                <div className="tramite-card info">
                    <p>✅ ¡Buen trabajo! No tienes módulos pendientes por solicitar.</p>
                    <p>Has solicitado todos tus certificados o no tienes módulos 100% aprobados aún. Revisa tu historial abajo.</p>
                </div>
            ) : (
                <form className="tramite-card" onSubmit={handleSubmit}>
                    <p>Selecciona el módulo del cual deseas solicitar tu certificado:</p>
                    <div className="form-row">
                        <label htmlFor="modulo-select">Módulo Aprobado:</label>
                        <select
                            id="modulo-select"
                            value={selectedModule}
                            onChange={(e) => setSelectedModule(e.target.value)}
                            disabled={isSubmitting}
                        >
                            {disponibles.map(mod => (
                                <option key={mod.modulo_id} value={mod.modulo_id}>
                                    {mod.nombre}
                                </option>
                            ))}
                        </select>
                    </div>
                    <button
                        type="submit"
                        className="btn-primary"
                        disabled={isSubmitting || !selectedModule}
                    >
                        {isSubmitting ? "Enviando..." : "Enviar Solicitud"}
                    </button>
                </form>
            )}
        </section>
    );
}

// --- Componente para la sección "Historial" ---
function HistorialTramites({ historial, loading }) {
    return (
        <section className="tramite-section historial-section">
            <h2><FaHistory /> Mi Historial de Solicitudes</h2>
            {loading ? (
                <p>Cargando historial...</p>
            ) : historial.length === 0 ? (
                <p>No has realizado ninguna solicitud de trámite todavía.</p>
            ) : (
                <div className="historial-grid">
                    {historial.map(item => (
                        <div key={item.tramite_id} className="tramite-card historial-card">
                            <div className="card-header">
                                <h4>{item.modulo_nombre}</h4>
                                <StatusBadge estado={item.estado} />
                            </div>
                            <p className="card-subtitle">
                                {item.tipo_tramite} | Solicitado: {new Date(item.fecha_solicitud).toLocaleDateString()}
                            </p>
                            
                            {item.observaciones_admin && (
                                <p className="card-obs">
                                    <strong>Observación:</strong> {item.observaciones_admin}
                                </p>
                            )}

                            {item.estado === 'Aprobado' && item.ruta_archivo && (
                                <a
                                    // La URL apunta a nuestra API de descarga segura
                                    href={`/api/descargar_tramite/${item.tramite_id}`}
                                    className="btn-primary download-btn"
                                    target="_blank" // Abre en nueva pestaña (opcional)
                                    rel="noopener noreferrer"
                                >
                                    <FaDownload /> Descargar Certificado
                                </a>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </section>
    );
}


// --- Componente Principal de la Página ---
export default function Tramites() {
    const [historial, setHistorial] = useState([]);
    const [disponibles, setDisponibles] = useState([]);
    const [loading, setLoading] = useState({ historial: true, disponibles: true });
    const [error, setError] = useState(null);

    // --- Funciones de Carga de Datos ---
    const fetchHistorial = async () => {
        try {
            const res = await fetch("/api/estudiante/tramites/historial", { credentials: "include" });
            if (!res.ok) throw new Error("No se pudo cargar el historial.");
            const data = await res.json();
            setHistorial(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(prev => ({ ...prev, historial: false }));
        }
    };

    const fetchDisponibles = async () => {
        try {
            const res = await fetch("/api/estudiante/tramites/disponibles", { credentials: "include" });
            if (!res.ok) throw new Error("No se pudo cargar los módulos disponibles.");
            const data = await res.json();
            setDisponibles(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(prev => ({ ...prev, disponibles: false }));
        }
    };

    // --- Carga inicial de datos ---
    useEffect(() => {
        setError(null);
        setLoading({ historial: true, disponibles: true });
        fetchHistorial();
        fetchDisponibles();
    }, []); // Se ejecuta solo una vez al montar el componente

    // --- Función para manejar la solicitud ---
    const handleSolicitar = async (modulo_id) => {
        setError(null);
        try {
            const res = await fetch("/api/estudiante/tramites/solicitar", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ modulo_id }),
                credentials: "include"
            });
            
            const data = await res.json();

            if (!res.ok) {
                // Si la API devuelve un error (ej. 409 Conflict), lo muestra
                throw new Error(data.error || "No se pudo enviar la solicitud.");
            }

            alert("¡Solicitud enviada con éxito!"); // Mensaje de éxito

            // ¡Importante! Refrescar los datos después de una solicitud exitosa
            setLoading({ historial: true, disponibles: true });
            fetchHistorial();
            fetchDisponibles();

        } catch (err) {
            console.error("Error al solicitar:", err);
            setError(err.message);
            alert(`Error: ${err.message}`); // Muestra el error
        }
    };

    return (
        <section className="tramites-page">
            <h1>Trámites Académicos 📜</h1>
            <p>Aquí puedes solicitar tus certificados de módulo y ver el estado de tus solicitudes.</p>

            {error && <p className="error-message">Error: {error}</p>}

            <SolicitarTramite
                disponibles={disponibles}
                loading={loading.disponibles}
                onSolicitar={handleSolicitar}
            />

            <hr className="section-divider" />

            <HistorialTramites
                historial={historial}
                loading={loading.historial}
            />
        </section>
    );
}