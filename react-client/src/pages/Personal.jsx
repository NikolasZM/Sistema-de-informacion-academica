import { useEffect, useState } from "react"

/* ----------------------------------------------------------- */
/* PEQUEÑO INPUT Reutilizable                                  */
/* ----------------------------------------------------------- */
function Input({ label, value, setValue, readOnly=false, type="text" }) {
  return (
    <div className="form-row">
      <label>{label}</label>
      <input
        type={type}
        value={value || ''} // Aseguramos que nunca sea undefined
        readOnly={readOnly}
        onChange={e => setValue && setValue(e.target.value)}
      />
    </div>
  )
}

/* ----------------------------------------------------------- */
/* PÁGINA PRINCIPAL                                            */
/* ----------------------------------------------------------- */
export default function Personal() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  // ---------------- DATOS SOLO LECTURA ----------------
  const [generalData, setGeneralData] = useState({
    nombre_completo: "",
    programa_estudio: "",
    codigo: "",
    dni: "",
    sexo: "",
    fecha_nacimiento: "",
  })

  // ---------------- DATOS EDITABLES (DOMICILIO y CELULAR) ----------------
  const [address, setAddress] = useState("")
  const [dep, setDep] = useState("")
  const [prov, setProv] = useState("")
  const [dist, setDist] = useState("")
  const [cell, setCell] = useState("")

  // ---------------- DATOS EDITABLES (CONTACTO 1) ----------------
  const [c1Name, setC1Name] = useState("")
  const [c1Par, setC1Par] = useState("")
  const [c1Tel, setC1Tel] = useState("")

  // ---------------- DATOS EDITABLES (CONTACTO 2) ----------------
  const [c2Name, setC2Name] = useState("")
  const [c2Par, setC2Par] = useState("")
  const [c2Tel, setC2Tel] = useState("")

  // 1. Cargar datos del estudiante al inicio
  useEffect(() => {
    setLoading(true)
    fetch("/api/estudiante/info", { credentials: "include" })
      .then(async res => {
        if (!res.ok) {
          throw new Error("Fallo al cargar datos del estudiante")
        }
        return res.json()
      })
      .then(data => {
        // Establecer datos generales (solo lectura)
        setGeneralData(data)
        
        // Establecer estados editables (domicilio y celular)
        setAddress(data.direccion)
        setDep(data.departamento)
        setProv(data.provincia)
        setDist(data.distrito)
        setCell(data.celular)
        
        // Establecer estados editables (contacto 1)
        setC1Name(data.c1_nombre)
        setC1Par(data.c1_parentesco)
        setC1Tel(data.c1_celular)
        
        // Establecer estados editables (contacto 2)
        setC2Name(data.c2_nombre)
        setC2Par(data.c2_parentesco)
        setC2Tel(data.c2_celular)
      })
      .catch(err => {
        console.error("Error de carga:", err)
        setError(err.message)
      })
      .finally(() => setLoading(false))
  }, [])


  /* Guardar los cambios */
  const handleSave = () => {
    setLoading(true)
    setError(null)
    
    // Solo enviamos los campos que el usuario puede editar.
    const payload = {
      direccion: address,
      departamento: dep,
      provincia: prov,
      distrito: dist,
      celular: cell,
      
      c1_nombre: c1Name,
      c1_parentesco: c1Par,
      c1_celular: c1Tel,
      
      c2_nombre: c2Name,
      c2_parentesco: c2Par,
      c2_celular: c2Tel,
    }

    fetch("/api/estudiante/info", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      credentials: "include",
    })
    .then(async res => {
      if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.error || "Fallo al guardar los datos.")
      }
      return res.json()
    })
    .then(data => {
      alert(data.message || "¡Datos guardados correctamente!")
    })
    .catch(err => {
      console.error("Error al guardar:", err)
      setError(err.message)
    })
    .finally(() => setLoading(false))
  }

  if (loading) return <p>Cargando información personal...</p>
  if (error) return <p style={{ color: "red" }}>Error: {error}</p>

  return (
    <section className="pers-page">

      {/* ---------- DATOS GENERALES (solo lectura) ---------- */}
      <h2>Datos Generales (Solo Lectura)</h2>
      <div className="form-grid">
        <Input label="Nombre completo" value={generalData.nombre_completo} readOnly />
        <Input label="Programa de estudio" value={generalData.programa_estudio} readOnly />
        <Input label="Código" value={generalData.codigo} readOnly />
        <Input label="DNI" value={generalData.dni} readOnly />
        <Input label="Sexo" value={generalData.sexo} readOnly />
        <Input label="Fecha de Nacimiento" value={generalData.fecha_nacimiento} readOnly />
      </div>

      {/* 💡 DOMICILIO ACTUAL Y CELULAR (EDITABLE) ------------------------ */}
      <h2>Domicilio y Contacto Principal (Editable)</h2>
      <div className="form-grid">
        {/* Estos campos ahora permiten edición */}
        <Input label="Dirección" value={address} setValue={setAddress} />
        <Input label="Departamento" value={dep} setValue={setDep} />
        <Input label="Provincia" value={prov} setValue={setProv} />
        <Input label="Distrito" value={dist} setValue={setDist} />
        <Input label="Celular / WhatsApp" value={cell} setValue={setCell} type="tel" />
      </div>

      {/* 💡 CONTACTO DE EMERGENCIA (EDITABLE) ------------------ */}
      <h2>Contactos de Emergencia (Editables)</h2>

      {/* Contacto 1 */}
      <h3>Contacto Principal de Emergencia</h3>
      <div className="form-grid">
        <Input label="Apellidos y nombres (C1)" value={c1Name} setValue={setC1Name}/>
        <Input label="Parentesco (C1)" value={c1Par} setValue={setC1Par}/>
        <Input label="Teléfono / celular (C1)" value={c1Tel} setValue={setC1Tel} type="tel" />
      </div>

      {/* Contacto 2 */}
      <h3>Contacto Secundario de Emergencia</h3>
      <div className="form-grid">
        <Input label="Apellidos y nombres (C2)" value={c2Name} setValue={setC2Name}/>
        <Input label="Parentesco (C2)" value={c2Par} setValue={setC2Par}/>
        <Input label="Teléfono / celular (C2)" value={c2Tel} setValue={setC2Tel} type="tel" />
      </div>

      {/* ----------- BOTÓN GUARDAR -------------------------- */}
      <div className="btn-row">
        <button className="save-btn" onClick={handleSave} disabled={loading}>
          {loading ? "Guardando..." : "Guardar Cambios"}
        </button>
      </div>

    </section>
  )
}