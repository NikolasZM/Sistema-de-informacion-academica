# ejecutar_todo.py
import sys
import os
import subprocess
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def ejecutar_script(nombre_script, descripcion):
    """Ejecuta un script y muestra el resultado"""
    print(f"\n{'='*60}")
    print(f"🔄 EJECUTANDO: {descripcion}")
    print(f"📁 Script: {nombre_script}")
    print(f"{'='*60}")
    
    try:
        # Verificar si el archivo existe
        if not os.path.exists(nombre_script):
            print(f"❌ Archivo no encontrado: {nombre_script}")
            return False
            
        # Ejecutar el script
        resultado = subprocess.run(
            [sys.executable, nombre_script], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        print(f"✅ {descripcion} - COMPLETADO")
        if resultado.stdout:
            print(f"   Output: {resultado.stdout.strip()}")
        
        time.sleep(1)  # Pequeña pausa entre scripts
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR en {nombre_script}: {e}")
        if e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        return False
    except Exception as e:
        print(f"❌ ERROR inesperado en {nombre_script}: {e}")
        return False

def main():
    print("🚀 INICIANDO CARGA COMPLETA DE LA BASE DE DATOS")
    print("⏰ Este proceso puede tomar varios minutos...")
    
    # Lista de scripts en orden de ejecución
    scripts = [
        ('salon.py', 'CREAR SALONES'),
        ('crear_docentes.py', 'CREAR DOCENTES'),
        ('crear_estudiantes.py', 'CREAR ESTUDIANTES'),
        ('crear_periodos_programas_modulos.py', 'CREAR PERIODOS, MÓDULOS Y PROGRAMAS (Estilismo y TI)'),
        ('agregar_programaciones.py', 'PROGRAMAR CLASES'),
        ('matricularEstudiante.py', 'MATRICULAR ESTUDIANTES'),
        ('asistencia.py', 'GENERAR ASISTENCIAS DE EJEMPLO')
    ]
    
    # Contadores
    exitosos = 0
    fallidos = 0
    
    # Ejecutar todos los scripts
    for script, descripcion in scripts:
        if ejecutar_script(script, descripcion):
            exitosos += 1
        else:
            fallidos += 1
            # Preguntar si continuar después de error
            continuar = input(f"\n⚠️  ¿Continuar con los siguientes scripts? (s/n): ")
            if continuar.lower() != 's':
                print("⏹️  Ejecución detenida por el usuario")
                break
    
    # Resumen final
    print(f"\n{'='*60}")
    print("📊 RESUMEN FINAL")
    print(f"{'='*60}")
    print(f"✅ Scripts exitosos: {exitosos}")
    print(f"❌ Scripts fallidos: {fallidos}")
    print(f"📈 Tasa de éxito: {(exitosos/len(scripts))*100:.1f}%")
    
    if fallidos == 0:
        print("🎉 ¡TODOS LOS SCRIPTS EJECUTADOS EXITOSAMENTE!")
        print("\n📦 Base de datos cargada con:")
        print("   • Salones, docentes y estudiantes")
        print("   • Periodos académicos")
        print("   • Programas de Estilismo y TI")
        print("   • Módulos y cursos")
        print("   • Matrículas de estudiantes")
        print("   • Programaciones de clases")
        print("   • Asistencias de ejemplo")
    else:
        print("⚠️  Algunos scripts fallaron. Revisa los errores arriba.")
    
    print(f"{'='*60}")

if __name__ == "__main__":
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('salon.py'):
        print("❌ Error: Debes ejecutar este script desde la carpeta 'db/'")
        print("💡 Usa: cd flask-backend/db && python ejecutar_todo.py")
        sys.exit(1)
    
    main()