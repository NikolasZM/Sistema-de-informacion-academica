// src/pages/Rendimiento.jsx
import { useEffect, useState } from "react"
import {
  FaCheckCircle, FaTimesCircle, FaClock, FaHourglassHalf,
  FaFileContract, FaPaperPlane
} from "react-icons/fa"

const NOTA_APROBATORIA = 12.5;

/* ---------------- Utilidad: icono + clase por estado ---------------- */
function estadoInfo(estado) {
  switch (estado) {
    case "Aprobado":    return { icon: <FaCheckCircle/>, cls: "status-ok",    label: "Aprobado" }
    case "Desaprobado": return { icon: <FaTimesCircle/>,  cls: "status-danger",  label: "Desaprobado" }
    case "En Curso":    return { icon: <FaHourglassHalf/>,cls: "status-review",  label: "En Curso" }
    default:            return { icon: <FaClock/>,        cls: "status-pending", label: "Pendiente" }
  }
}

/* ---------------- Fila de curso en TABLA ---------------- */
function CourseItem({ curso, idx }) {
  const info = estadoInfo(curso.estado)
  const nota = (curso.nota_final !== null && curso.nota_final !== undefined)
    ? Number(curso.nota_final).toFixed(2)
    : "N / A"
  
  const notaClass = nota === "N / A" 
    ? "" 
    : (nota >= NOTA_APROBATORIA ? "text-success" : "text-danger");

  return (
    <tr>
      <td>{idx}</td>
      <td>{curso.nombre}</td>
      <td>
        <span className={`status-badge ${info.cls}`}>
          {info.icon} {info.label}
        </span>
      </td>
      <td className={notaClass}>{nota}</td>
    </tr>
  )
}

/* ---------------- Tarjeta de Módulo (encabezado + tabla) ---------------- */
function ModuloCard({ modulo, onNavigate }) {
  const modInfo = estadoInfo(modulo.estado_modulo)
  const moduloTitle = `Módulo ${modulo.num_modulo}: ${modulo.nombre}`;

  let actionFooter = null
  if (modulo.puede_solicitar_tramite) {
    actionFooter = (
      <button className="btn-primary" onClick={() => onNavigate("tramites")}>
        <FaFileContract /> Solicitar Certificado
      </button>
    )
  } else if (modulo.estado_tramite) {
    let icon = <FaPaperPlane />
    if (modulo.estado_tramite === "Aprobado") icon = <FaCheckCircle />
    actionFooter = (
      <div className="tramite-status">
        {icon} Trámite: <strong>{modulo.estado_tramite}</strong>
      </div>
    )
  }

  return (
    <div className="module-card">
      <header className="card-header">
        <h3>{moduloTitle}</h3>
        <span className={`status-badge ${modInfo.cls}`}>
          {modInfo.icon} {modInfo.label}
        </span>
      </header>

      <div className="grades-wrapper">
        <table className="grades-table rend-table">
          <thead>
            <tr>
              <th>N°</th>
              <th>Unidad Didáctica</th>
              <th>Estado</th>
              <th>Nota Final</th>
            </tr>
          </thead>
          <tbody>
            {modulo.cursos && modulo.cursos.length > 0 ? (
              modulo.cursos.map((curso, i) => (
                <CourseItem
                  key={curso.curso_id ?? `${modulo.modulo_id}-${i}`}
                  curso={curso}
                  idx={i + 1}
                />
              ))
            ) : (
              <tr>
                <td colSpan="4" className="text-center">
                  Este módulo no tiene cursos asignados.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {actionFooter && <footer className="card-footer">{actionFooter}</footer>}
    </div>
  )
}

/* ---------------- Página principal ---------------- */
export default function Rendimiento({ onNavigate }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    
    fetch("/api/estudiante/avance_curricular", { credentials: "include" })
      .then(async (res) => {
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.error || "No se pudo cargar el avance curricular.")
        }
        return res.json()
      })
      .then((fetched) => setData(fetched))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p>Cargando tu avance curricular…</p>
  if (error)    return <p className="error-message">Error: {error}</p>
  if (!data || !data.modulos) return <p>No se encontraron datos de avance curricular.</p>

  return (
    <section className="avance-page">
      <h1>Rendimiento y Avance Curricular</h1>
      
      {/* ✅ Ahora con <strong> en lugar de ** ** */}
      <p className="programa-title">
        Programa: <strong>{data.programa_nombre || 'No Asignado'}</strong>
      </p>

      {/* ✅ Leyenda con nota mínima */}
      <div className="legend-container">
        <span className="status-badge status-ok">
          <FaCheckCircle/> Aprobado (≥ {NOTA_APROBATORIA})
        </span>
        <span className="status-badge status-review">
          <FaHourglassHalf/> En Curso
        </span>
        <span className="status-badge status-danger">
          <FaTimesCircle/> Desaprobado
        </span>
        <span className="status-badge status-pending">
          <FaClock/> Pendiente
        </span>
      </div>

      <div className="module-list">
        {data.modulos.length > 0 ? (
          data.modulos.map((m) => (
            <ModuloCard key={m.modulo_id} modulo={m} onNavigate={onNavigate} />
          ))
        ) : (
          <p>No se encontraron módulos para este programa.</p>
        )}
      </div>
    </section>
  )
}
