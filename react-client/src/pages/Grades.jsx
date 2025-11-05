import { useEffect, useState } from "react"
import { FaChevronDown, FaChevronUp, FaCheckCircle, FaTimesCircle, FaClock, FaChartBar, FaBook, FaThumbsUp, FaThumbsDown } from "react-icons/fa"

/* ------------------------------------------------------------------ */
/* Tarjeta de Resumen del Período (NUEVO)                             */
/* ------------------------------------------------------------------ */
function GradesSummaryCard({ resumen }) {
    return (
        <div className="summary-card-grid">
            <div className="summary-card">
                <FaChartBar className="summary-icon" />
                <div className="summary-content">
                    <span className="summary-value">{resumen.promedio_simple || 'N/A'}</span>
                    <span className="summary-label">Promedio Simple</span>
                </div>
            </div>
            <div className="summary-card">
                <FaBook className="summary-icon" />
                <div className="summary-content">
                    <span className="summary-value">{resumen.total_cursos}</span>
                    <span className="summary-label">Cursos Totales</span>
                </div>
            </div>
            <div className="summary-card">
                <FaThumbsUp className="summary-icon status-ok" />
                <div className="summary-content">
                    <span className="summary-value">{resumen.aprobados}</span>
                    <span className="summary-label">Aprobados</span>
                </div>
            </div>
            <div className="summary-card">
                <FaThumbsDown className="summary-icon status-danger" />
                <div className="summary-content">
                    <span className="summary-value">{resumen.desaprobados}</span>
                    <span className="summary-label">Desaprobados</span>
                </div>
            </div>
        </div>
    )
}

/* ------------------------------------------------------------------ */
/* Sub-fila (detalle de notas)                                        */
/* ------------------------------------------------------------------ */
function GradeDetailRows({ notas }) {
    return (
        <tr className="grade-detail">
            <td colSpan={5}> {/* ⬅️ colSpan = 5, coincide con la cabecera */}
                <div className="note-detail-wrapper">
                    <h4>Detalle de Evaluaciones</h4>
                    {notas.length > 0 ? (
                        <ul className="note-list">
                            {notas.map(n => (
                                <li key={n.id}>
                                    <span className="label">{n.tipo} ({n.fecha})</span>
                                    <span className="value">{n.valor.toFixed(2)}</span>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="no-notes">No hay evaluaciones detalladas registradas.</p>
                    )}
                </div>
            </td>
        </tr>
    )
}

/* ------------------------------------------------------------------ */
/* Fila principal (Mejorada)                                          */
/* ------------------------------------------------------------------ */
function CourseGradeRow({ index, curso }) {
    const [open, setOpen] = useState(false)

    const { nombre, codigo, promedio_final, estado, notas_detalle } = curso

    // Define el estilo de la nota final y el badge de estado
    let finalGradeClass = "grade-value ";
    let statusBadge = null;

    if (estado === "Aprobado") {
        finalGradeClass += "approved";
        statusBadge = <span className="status-badge ok"><FaCheckCircle /> Aprobado</span>;
    } else if (estado === "Desaprobado") {
        finalGradeClass += "failed";
        statusBadge = <span className="status-badge danger"><FaTimesCircle /> Desaprobado</span>;
    } else { // Pendiente
        finalGradeClass += "pending";
        statusBadge = <span className="status-badge pending"><FaClock /> Pendiente</span>;
    }

    return (
        <>
            <tr className="grade-row">
                <td>{index + 1}</td>
                <td>{codigo}</td>
                <td>{nombre}</td>
                <td className="status-cell">
                    {statusBadge}
                </td>
                <td className="final-grade-cell">
                    <strong className={finalGradeClass}>
                        {promedio_final !== null ? promedio_final.toFixed(2) : 'N/A'}
                    </strong>
                </td>
                <td>
                    <button className="grade-btn" onClick={() => setOpen(v => !v)}>
                        {open ? <FaChevronUp /> : <FaChevronDown />}
                    </button>
                </td>
            </tr>

            {open && <GradeDetailRows notas={notas_detalle} />}
        </>
    )
}

/* ------------------------------------------------------------------ */
/* Página completa (Actualizada)                                      */
/* ------------------------------------------------------------------ */
export default function Grades() {
    const [periods, setPeriods] = useState([])
    const [selectedPeriod, setSelectedPeriod] = useState(null)
    
    // El estado 'data' ahora almacena el objeto completo de la API
    const [data, setData] = useState(null) 
    
    const [loadingPeriods, setLoadingPeriods] = useState(true)
    const [loadingCourses, setLoadingCourses] = useState(false)
    const [error, setError] = useState(null)

    // 1. Cargar la lista de períodos disponibles
    useEffect(() => {
        setLoadingPeriods(true)
        fetch("/api/estudiante/periodos", { credentials: "include" })
            .then(res => {
                if (!res.ok) throw new Error("No se pudo cargar la lista de períodos.");
                return res.json();
            })
            .then(data => {
                setPeriods(data)
                if (data.length > 0) {
                    setSelectedPeriod(data[0].periodo_id)
                }
            })
            .catch(err => {
                console.error("Error cargando períodos:", err)
                setError(err.message)
            })
            .finally(() => setLoadingPeriods(false))
    }, [])

    // 2. Cargar cursos y notas cuando cambia el período seleccionado
    useEffect(() => {
        if (!selectedPeriod) {
            setData(null)
            return
        }

        setLoadingCourses(true)
        setError(null)
        setData(null) // Limpia datos anteriores mientras carga
        
        fetch(`/api/estudiante/periodo/${selectedPeriod}/calificaciones`, { credentials: "include" })
            .then(async res => {
                if (!res.ok) {
                    const err = await res.json().catch(() => ({}))
                    throw new Error(err.error || "Error al cargar calificaciones.")
                }
                return res.json()
            })
            .then(fetchedData => {
                setData(fetchedData) // Guarda el objeto {resumen, cursos}
            })
            .catch(err => {
                console.error("Error cargando calificaciones:", err)
                setError(err.message)
                setData(null)
            })
            .finally(() => setLoadingCourses(false))
    }, [selectedPeriod])
    
    const selectedPeriodCode = periods.find(p => p.periodo_id === selectedPeriod)?.codigo || '...'

    return (
        <section className="grades-page">
            <h1>Mis Calificaciones 📊</h1>

            {/* --- Selector de Período --- */}
            {loadingPeriods ? (
                <p>Cargando períodos...</p>
            ) : periods.length === 0 ? (
                <p>No tiene matrículas históricas o activas.</p>
            ) : (
                <div className="period-selector-card">
                    <label htmlFor="periodG">Seleccionar Período Académico:</label>
                    <select
                        id="periodG"
                        value={selectedPeriod ?? ""}
                        onChange={e => setSelectedPeriod(Number(e.target.value))}
                    >
                        {periods.map(p => (
                            <option key={p.periodo_id} value={p.periodo_id}>
                                {p.codigo}
                            </option>
                        ))}
                    </select>
                </div>
            )}
            
            <h2>Resumen del Período: {selectedPeriodCode}</h2>

            {/* --- Contenido Principal (Resumen y Tabla) --- */}
            {loadingCourses ? (
                <p>Cargando notas...</p>
            ) : error ? (
                <p className="error-message">Error: {error}</p>
            ) : data ? (
                <>
                    {/* Tarjeta de Resumen */}
                    <GradesSummaryCard resumen={data.resumen} />
                    
                    {/* Tabla de Cursos */}
                    <div className="grades-wrapper">
                        <table className="grades-table">
                            <thead>
                                <tr>
                                    <th>Nº</th>
                                    <th>Código</th>
                                    <th>Unidad Didáctica</th>
                                    <th>Estado</th>
                                    <th>Promedio Final</th>
                                    <th>Detalle</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.cursos.length > 0 ? (
                                    data.cursos.map((c, i) => (
                                        <CourseGradeRow key={c.curso_id} index={i} curso={c} />
                                    ))
                                ) : (
                                    <tr><td colSpan="6">No hay calificaciones disponibles en este período.</td></tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </>
            ) : (
                !loadingPeriods && <p>Seleccione un período para ver sus notas.</p>
            )}
        </section>
    )
}