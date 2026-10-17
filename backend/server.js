
require("dotenv").config();

const express = require("express");
const cors = require("cors");


const app = express();

app.use(cors());
app.use(express.json());

const { Pool } = require("pg");

const pool = process.env.DATABASE_URL
  ? new Pool({
      connectionString: process.env.DATABASE_URL,
      ssl: { rejectUnauthorized: false },
    })
  : new Pool({
      host: process.env.DB_HOST || "localhost",
      port: Number(process.env.DB_PORT || 5432),
      database: process.env.DB_NAME || "vehicle_analytics",
      user: process.env.DB_USER || "postgres",
      password: process.env.DB_PASSWORD,
    });

app.get("/", (req, res) => {
  res.send("Vehicle Analytics API is running!");
});

app.get("/api/health", (req, res) => {
  res.json({ status: "ok", service: "vehicle-analytics-api" });
});

app.get("/api/db-health", async (req, res) => {
  try {
    const result = await pool.query(
      "SELECT current_database() AS database, NOW() AS server_time"
    );

    res.json({
      status: "connected",
      ...result.rows[0],
    });
  } catch (error) {
    console.error("Database connection failed:", error.message);
    res.status(500).json({
      status: "error",
      message: "Could not connect to PostgreSQL",
    });
  }
});


app.get("/api/events", async (req, res) => {
  try {
    const result = await pool.query(
      `SELECT id, vehicle_id, vehicle_type, color,
              timestamp, direction, source_id
       FROM vehicle_events
       ORDER BY timestamp DESC
       LIMIT 100`
    );

    res.json(result.rows);
  }  catch (error) {
  console.error("Failed to fetch events:", error);
  res.status(500).json({
    error: "Could not fetch vehicle events",
    details: error.message,
  });
}
});


app.post("/api/events", async (req, res) => {
  const {
    vehicle_id,
    vehicle_type,
    color,
    direction,
    source_id,
  } = req.body;

  if (!Number.isInteger(vehicle_id) || vehicle_id <= 0) {
    return res.status(400).json({
      error: "vehicle_id must be a positive integer",
    });
  }

  try {
    const result = await pool.query(
      `INSERT INTO vehicle_events
        (vehicle_id, vehicle_type, color, direction, source_id)
       VALUES ($1, $2, $3, $4, $5)
       RETURNING id, vehicle_id, vehicle_type, color,
                 timestamp, direction, source_id`,
      [
        vehicle_id,
        vehicle_type || "Unknown",
        color || "Unknown",
        direction || "Unknown",
        source_id || "Test_Source",
      ]
    );

    res.status(201).json(result.rows[0]);
  } catch (error) {
    console.error("Failed to insert event:", error.message);
    res.status(500).json({
      error: "Could not save vehicle event",
    });
  }
});



const PORT = Number(process.env.PORT || 5000);

app.listen(PORT, () => {
  console.log(`API running at http://localhost:${PORT}`);
});
