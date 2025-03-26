# IngestarCitas: Lectura de S3 y creación de Delta Table

from pyspark.sql import SparkSession

# Crea sesión Spark si es necesario (Databricks normalmente ya la tiene)
spark = SparkSession.builder.getOrCreate()

# Ruta del archivo CSV en S3 (asegúrate que coincide con lo que subes desde Lambda)
ruta_s3 = "s3://citas-pelu/citas.csv"

# Cargar el CSV
df = spark.read.format("csv").option("header", "true").load(ruta_s3)

# Mostrar por si quieres revisar el contenido (opcional)
df.show()

# Escribir en formato Delta como tabla permanente (si no existe, la crea)
df.write.format("delta").mode("overwrite").saveAsTable("citas_pelu")

print("✅ Tabla Delta creada como 'citas_pelu'")
