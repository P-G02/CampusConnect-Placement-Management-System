-- Migration 004: Deduplicate and enforce unique primary key on student_skill junction table

-- Step 1: Remove exact duplicate rows, keeping one copy per (student_id, skill_id)
DELETE FROM student_skill a USING (
    SELECT min(ctid) as min_ctid, student_id, skill_id
    FROM student_skill 
    GROUP BY student_id, skill_id HAVING count(*) > 1
) b
WHERE a.student_id = b.student_id 
  AND a.skill_id = b.skill_id 
  AND a.ctid <> b.min_ctid;

-- Step 2: Ensure student_id and skill_id are NOT NULL
ALTER TABLE student_skill ALTER COLUMN student_id SET NOT NULL;
ALTER TABLE student_skill ALTER COLUMN skill_id SET NOT NULL;

-- Step 3: Add PRIMARY KEY constraint if not already present
ALTER TABLE student_skill ADD CONSTRAINT student_skill_pkey PRIMARY KEY (student_id, skill_id);
