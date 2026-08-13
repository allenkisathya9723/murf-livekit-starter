import { NextResponse } from 'next/server';
import { DatabaseSync } from 'node:sqlite';
import path from 'path';

export const revalidate = 0;

export async function GET() {
  try {
    const dbPath = path.resolve(process.cwd(), '../backend/data/janmitra.db');
    const database = new DatabaseSync(dbPath);
    
    // Ensure table exists in case frontend API is called before backend init
    database.exec(`
      CREATE TABLE IF NOT EXISTS call_analytics (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          call_id TEXT NOT NULL,
          channel TEXT NOT NULL DEFAULT 'browser',
          outcome TEXT NOT NULL DEFAULT 'FAILED',
          language TEXT DEFAULT 'English',
          duration_seconds INTEGER DEFAULT 0,
          started_at TEXT NOT NULL,
          ended_at TEXT NOT NULL
      );
    `);

    const totalStmt = database.prepare('SELECT COUNT(*) AS count FROM call_analytics');
    const totalRow = totalStmt.get() as { count: number };

    const successStmt = database.prepare("SELECT COUNT(*) AS count FROM call_analytics WHERE UPPER(outcome) = 'SUCCESS'");
    const successRow = successStmt.get() as { count: number };

    const failedStmt = database.prepare("SELECT COUNT(*) AS count FROM call_analytics WHERE UPPER(outcome) = 'FAILED'");
    const failedRow = failedStmt.get() as { count: number };

    const recentStmt = database.prepare(
      'SELECT id, call_id, channel, outcome, language, duration_seconds, started_at, ended_at FROM call_analytics ORDER BY id DESC LIMIT 10'
    );
    const recentRows = recentStmt.all();

    database.close();

    return NextResponse.json({
      total_calls: totalRow?.count || 0,
      successful_calls: successRow?.count || 0,
      failed_calls: failedRow?.count || 0,
      recent_calls: recentRows || []
    });
  } catch (error: any) {
    return NextResponse.json({
      total_calls: 0,
      successful_calls: 0,
      failed_calls: 0,
      recent_calls: [],
      error: error.message
    }, { status: 500 });
  }
}
