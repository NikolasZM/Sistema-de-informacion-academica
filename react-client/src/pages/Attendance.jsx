import { useEffect, useState } from "react"
import { FaChevronDown, FaChevronUp, FaExclamationTriangle, FaCheckCircle, FaBan } from "react-icons/fa"

const RETIRO_PERCENT = 30 // Límite de inasistencia
const ALERTA_PERCENT = 25 // Empezar a mostrar alerta amarilla

/* ------------------------------------------------------- */
/* Tarjeta de Resumen (NUEVO)                              */
/* ------------------------------------------------------- */
function AttendanceWarningCard({ courses }) {
    const cursos_en_riesgo = courses.filter(
        c => !c.retirado && c.porcentaje_inasistencia >= ALERTA_PERCENT
    ).length

    const cursos_retirados = courses.filter(c => c.retirado).length

    if (cursos_en_riesgo === 0 && cursos_retirados === 0) {
        return (
            <div className="att-card status-ok">
                <FaCheckCircle />
                <div className="card-content">
                    <h4>¡Todo en orden!</h4>
                    <p>No tienes cursos en riesgo de retiro por inasistencia. ¡Sigue así!</p>
                </div>
            </div>
        )
    }

    return (
        <div className="att-card status-danger">
            <FaExclamationTriangle />
            <div className="card-content">
                <h4>¡Atención Requerida!</h4>
                <p>
                    Tienes <strong>{cursos_retirados} curso(s) RETIRADOS</strong> y <strong>{cursos_en_riesgo} curso(s) EN RIESGO</strong> por inasistencia.
                    Revisa el detalle a continuación.
                </p>
            </div>
        </div>
    )
}


/* ------------------------------------------------------- */
/* Fila-detalle: una fila por cada asistencia/inasistencia */
/* ------------------------------------------------------- */
function AbsenceDetailRows({ details }) {
    if (details.length === 0) {
        return (
            <tr className="att-detail">
                <td colSpan={8} className="no-absences-cell">
                    No hay registros de asistencia (asistencias o faltas) para este curso.
                </td>
            </tr>
        )
    }

    return details.map((a, i) => (
        <tr key={i} className={`att-detail detail-${a.estado} ${a.justificada ? 'detail-justificada' : ''}`}>
            <td></td> {/* Columna vacía para alinear */}
            <td className="date">{a.fecha}</td>
            <td className="status-cell">
                {a.estado === 'asistio' ? 'Asistió' : (a.justificada ? 'Falta Justificada' : 'FALTA')}
            </td>
            <td colSpan={5} className="detail-reason-cell">{a.observacion || (a.justificada ? 'Justificación aceptada.' : 'Sin observación.')}</td>
        </tr>
    ))
}

/* ------------------------------------------------------- */
/* Fila principal del Curso (Mejorada)                     */
/* ------------------------------------------------------- */
function CourseRow({ idx, item }) {
    const [open, setOpen] = useState(false)

    const { 
        retirado, 
        porcentaje_inasistencia, 
        faltas_contadas, 
        max_faltas_permitidas,
        sesiones_totales
    } = item;

    // Determina el estado visual
    const en_riesgo = !retirado && porcentaje_inasistencia >= ALERTA_PERCENT;
    
    let rowClass = 'att-row ';
    if (retirado) rowClass += 'att-retired';
    else if (en_riesgo) rowClass += 'att-warning';
    else rowClass += 'att-ok';

    const missBarStyle = { width: `${Math.min(porcentaje_inasistencia, 100)}%` }

    return (
        <>
            <tr className={rowClass}>
                <td>{idx + 1}</td>
                <td>{item.codigo}</td>
                <td>{item.nombre}</td>
                
                {/* DATO CORREGIDO */}
                <td><strong>{sesiones_totales}</strong></td>
                
                {/* Faltas Contabilizadas / Máx. Permitidas */}
                <td className="text-center">
                    <strong>{faltas_contadas}</strong> / {max_faltas_permitidas}
                </td>
                
                {/* Porcentaje de Inasistencia y Barra */}
                <td className="percent-cell">
                    <div className="bar-bg">
                        <div
                            className={`bar-miss ${retirado ? 'bar-alert' : (en_riesgo ? 'bar-warn' : '')}`}
                            style={missBarStyle}
                        ></div>
                        <div className="bar-label">
                            {porcentaje_inasistencia}%
                        </div>
                    </div>
                </td>
                
                {/* Estado Final (más visible) */}
                <td className="status-cell">
                    {retirado ? (
                        <span className="status-badge retired"><FaBan /> RETIRADO</span>
                    ) : en_riesgo ? (
                        <span className="status-badge warning"><FaExclamationTriangle /> EN RIESGO</span>
                    ) : (
                        <span className="status-badge ok"><FaCheckCircle /> En Regla</span>
                    )}
                </td>

                {/* Botón de detalle */}
                <td>
                    <button className="att-btn" onClick={() => setOpen(v => !v)}>
                        {open ? <FaChevronUp /> : <FaChevronDown />}
                    </button>
                </td>
            </tr>

            {open && <AbsenceDetailRows details={item.asistencias_detalle} />}
        </>
    )
}

/* ------------------------------------------------------- */
/* Página completa (Actualizada)                           */
/* ------------------------------------------------------- */
export default function Attendance() {
    const [periods, setPeriods] = useState([])
    const [selectedPeriod, setSelectedPeriod] = useState(null)
    const [courses, setCourses] = useState([])
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

    // 2. Cargar asistencias cuando cambia el período seleccionado
    useEffect(() => {
        if (!selectedPeriod) {
            setCourses([])
            return
        }

        setLoadingCourses(true)
        setError(null)
        
        fetch(`/api/estudiante/periodo/${selectedPeriod}/asistencias`, { credentials: "include" })
            .then(async res => {
                if (!res.ok) {
                    const err = await res.json().catch(() => ({}))
                    throw new Error(err.error || "Error al cargar asistencias.")
                }
                return res.json()
            })
            .then(data => {
                setCourses(data.cursos)
            })
            .catch(err => {
                console.error("Error cargando asistencias:", err)
                setError(err.message)
                setCourses([])
            })
            .finally(() => setLoadingCourses(false))
    }, [selectedPeriod])
    
    const selectedPeriodCode = periods.find(p => p.periodo_id === selectedPeriod)?.codigo || '...'

    return (
        <section className="att-page">
            <h1>Registro de Asistencias 📋</h1>
            
            {/* Selector de Período */}
            {loadingPeriods ? (
                <p>Cargando períodos...</p>
            ) : periods.length === 0 ? (
                <p>No tiene matrículas activas o históricas.</p>
            ) : (
                <div className="period-selector-card">
                    <label>Seleccionar Período Académico:</label>
                    <select
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

            <h2>Detalle del Período: {selectedPeriodCode}</h2>
            
            {loadingCourses ? (
                <p>Cargando asistencias...</p>
            ) : error ? (
                <p className="error-message">Error: {error}</p>
            ) : (
                <>
                    {/* NUEVA TARJETA DE RESUMEN */}
                    <AttendanceWarningCard courses={courses} />

                    <div className="att-wrapper">
                        <p className="att-legend">
                            Una Unidad Didáctica (Curso) se considera <strong>RETIRADA</strong> si el porcentaje de inasistencias
                            (faltas no justificadas) es <strong>mayor al {RETIRO_PERCENT}%</strong> del total de sesiones programadas.
                        </p>
                        <table className="att-table">
                            <thead>
                                <tr>
                                    <th>Nº</th>
                                    <th>Código</th>
                                    <th>Unidad Didáctica</th>
                                    <th>Sesiones Totales</th>
                                    <th>Faltas (Real/Máx)</th>
                                    <th>% Inasist.</th>
                                    <th>Estado Final</th>
                                    <th>Detalle</th>
                                s</tr>
                            </thead>
                            <tbody>
                                {courses.length > 0 ? (
                                    courses.map((it, i) => <CourseRow key={it.curso_id} idx={i} item={it} />)
                                ) : (
                                    <tr><td colSpan="8">No hay datos de asistencia disponibles para este período.</td></tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </>
            )}
        </section>
    )
}