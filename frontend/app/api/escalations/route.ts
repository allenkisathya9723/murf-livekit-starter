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
      CREATE TABLE IF NOT EXISTS escalations (
          reference_id TEXT PRIMARY KEY,
          created_at TEXT NOT NULL,
          caller_id TEXT,
          reason TEXT NOT NULL,
          summary TEXT NOT NULL,
          what_checked TEXT NOT NULL,
          urgency TEXT NOT NULL,
          language TEXT NOT NULL,
          preferred_follow_up TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'OPEN'
      );
    `);

    const query = database.prepare(
      'SELECT reference_id, created_at, caller_id, reason, summary, what_checked, urgency, language, preferred_follow_up, status FROM escalations ORDER BY created_at DESC'
    );
    const rows = query.all();
    database.close();
    return NextResponse.json({ escalations: rows });
  } catch (error: any) {
    return NextResponse.json({ escalations: [], error: error.message }, { status: 500 });
  }
}
