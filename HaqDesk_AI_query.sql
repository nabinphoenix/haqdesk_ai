SELECT * FROM messages;


SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';


SELECT 'Users' as "Table", count(*) as "Total" FROM users
UNION ALL
SELECT 'Messages', count(*) FROM messages
UNION ALL
SELECT 'Conversations', count(*) FROM conversations
UNION ALL
SELECT 'Customers', count(*) FROM customers;





select * from businesses;
SELECT id, name FROM businesses;

SELECT id, filename, status FROM knowledge_documents;

SELECT COUNT(*) FROM knowledge_chunks WHERE document_id = 2;

DELETE FROM knowledge_chunks WHERE document_id = 1;
DELETE FROM knowledge_documents WHERE id = 1;



SELECT id, ai_draft, ai_language FROM messages WHERE ai_draft IS NOT NULL LIMIT 5;

SELECT id, content, ai_draft FROM messages ORDER BY timestamp DESC LIMIT 5;


SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'messages';


ADD COLUMN IF NOT EXISTS google_id VARCHAR UNIQUE;



SELECT DISTINCT role FROM users;


ALTER TABLE users
    ADD COLUMN IF NOT EXISTS provider VARCHAR NOT NULL DEFAULT 'local',
    ADD COLUMN IF NOT EXISTS google_id VARCHAR,
    ADD COLUMN IF NOT EXISTS avatar_url VARCHAR,
    ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_id
    ON users (google_id)
    WHERE google_id IS NOT NULL;

ALTER TABLE users
    ALTER COLUMN business_id DROP NOT NULL;

UPDATE users
SET role = 'business_admin'
WHERE role NOT IN ('super_admin','business_admin','agent','supervisor');


SELECT * FROM users;


UPDATE users
SET role = 'super_admin',
    business_id = NULL
WHERE email = 'admin.haqdesk.ai@gmail.com';


UPDATE users
SET role = 'business_admin'
WHERE email = 'nabinepali012@gmail.com';

UPDATE users
SET role = 'agent'
WHERE email = 'samir@haqdesk.ai';

UPDATE users
SET role = 'agent'
WHERE email = 'sita@haqdesk.ai';

TRUNCATE TABLE users, businesses RESTART IDENTITY CASCADE;

INSERT INTO businesses (name)
VALUES ('Tech Suru')
RETURNING id;


-- Nabin Nepali: HaqDesk AI Super Admin
UPDATE users
SET role = 'super_admin',
    business_id = NULL,
    status = 'online'
WHERE email = 'admin.haqdesk.ai@gmail.com';


-- Lakpa: Tech Suru Business Admin
UPDATE users
SET name = 'Lakpa',
    role = 'business_admin',
    business_id = 1,
    status = 'online'
WHERE email = 'nabinepali012@gmail.com';


SELECT 
    u.id,
    u.name,
    u.email,
    u.role,
    u.business_id,
    b.name AS business_name,
    u.status,
    u.provider,
    u.email_verified
FROM users u
LEFT JOIN businesses b ON u.business_id = b.id
ORDER BY u.id;

SELECT * FROM users;


UPDATE users
SET role = 'super_admin'
WHERE email = 'admin.haqdesk.ai@gmail.com';


INSERT INTO businesses (name)
VALUES ('Tech Suru')
RETURNING id;


SELECT id, name
FROM businesses
WHERE name = 'Tech Suru';


SELECT id, name, email, role, business_id, provider, email_verified
FROM users
ORDER BY id;


UPDATE users
SET name = 'Nabin Nepali',
    role = 'super_admin',
    business_id = NULL,
    status = 'online'
WHERE email = 'admin.haqdesk.ai@gmail.com';



SELECT id, platform, sender_id, content, timestamp 
FROM messages 
ORDER BY timestamp DESC 
LIMIT 10;

SELECT id, customer_id, platform, status, created_at 
FROM conversations 
ORDER BY created_at DESC 
LIMIT 10;


SELECT id, business_id, platform, status, page_id 
FROM integrations;

SELECT column_name FROM information_schema.columns WHERE table_name = 'conversations';


SELECT column_name FROM information_schema.columns WHERE table_name = 'integrations';

SELECT * FROM conversations ORDER BY id DESC LIMIT 5;


SELECT * FROM customers ORDER BY id DESC LIMIT 5;

SELECT * FROM businesses;

SELECT id, business_id, platform, status, metadata_json FROM integrations;

SELECT id, name, email, role, business_id FROM users;


SELECT id, business_id, platform, page_id, page_name, status FROM integrations;

INSERT INTO integrations (business_id, platform, page_id, page_name, access_token, status, created_at)
VALUES (
  1,
  'facebook',
  '871242899413570',
  'Tech Suru',
  'EAA1ZCgTX6sIUBRhRLCuXDnTyLSZAMdXBgHPZAks7d1nfSf063JDCQThjAqWrSpGAMrvtWYqNJjfpStgPj35vXClHn8I0hd8ZCz2d0NbCIc8QvYlrHyUl01OrUjEqwmpBUCl6g1aPP4Yvg8fhwq4VTR8o5dLwOOdgomHIS2pQBzJOkhdTLzK2DrfsrsrOPQXmBNCGDgZDZD',
  'active',
  NOW()
);

INSERT INTO integrations (business_id, platform, page_id, page_name, access_token, status, created_at)
VALUES (
  1,
  'instagram',
  '17841460555520897',
  'Tech Suru',
  'IGAASBMDqbUepBZAFpVSlZAZATDA0REwwMS1ITlpXM2FQRklRWVgzQ3NSZAS1fSW85ZA05EZA3A4ZAlJubWVjRGlHMkRsRVJTT0E4QzNobTdrYy1MbHJGT0pCUGRvU2FSUHV1WmppMVBacUVKV0xyT1d6a1dnd1NzRVlhdFNOUUVVcm5TVQZDZD',
  'active',
  NOW()
);

INSERT INTO integrations (business_id, platform, page_id, page_name, access_token, status, created_at)
VALUES (
  1,
  'whatsapp',
  '1204810899374269',
  'Tech Suru',
  'EAAR9ZBFgHwPkBRoZCXW06MZAPYniO5S5eF7a7MmeCyZCZAAkmOl2HNy1prX36JpwGipdTu5qbeQZADZAXoSAqRR0kahtt4XFAosMzxX8D1FwV4ZCk1XpL6Me9FjfgaskhHfODy7hi79F6W8UGRTSIFEVpGadX0v4dOU2p53adrAeCARkI3ZBEZBrLeBR6CwtzBLLImqm3iDX31A58AJEVxiOXx4AcQTgvz2MtN5ORikfPoZBLLAiCudZCmGMZAys4W9bGQV42V0pAgQJQhvETydyBHxMShVwZD',
  'active',
  NOW()
);


INSERT INTO users (name, email, hashed_password, role, business_id, provider, email_verified, created_at)
VALUES (
  'Tek Khatri',
  'techsuru1@gmail.com',
  '$2b$12$4Wtk13xl6zuC9dw9bDAAI.eshqEmxWZ7gRPYfD/KjuMAdEokxsaKK',
  'business_admin',
  1,
  'local',
  true,
  NOW()
);

SELECT id, name, email, role, business_id FROM users;

UPDATE users 
SET hashed_password = '$2b$12$T1fMnpIMcI5wbr1ZmQQszOyz.2SSsTby5Rq5Hk6ddu5WeCwVDvYcy'
WHERE email = 'techsuru1@gmail.com';


UPDATE users 
SET business_id = 1, role = 'business_admin'
WHERE email = 'techsuru1@gmail.com';


ALTER TABLE businesses ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE;

SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'businesses';

select * from users;



SELECT column_name FROM information_schema.columns 
WHERE table_name = 'conversations';


SELECT id, business_id, customer_id, status FROM conversations;

SELECT id, conversation_id, sender_type, sender_id, content 
FROM messages 
ORDER BY id DESC 
LIMIT 5;

SELECT id, conversation_id, sender_type, content, timestamp 
FROM messages 
ORDER BY timestamp DESC 
LIMIT 10;

SELECT id, business_id, customer_id, status FROM conversations WHERE business_id = 1;



UPDATE users 
SET hashed_password = '$2b$12$flS85HYLIREw8Qkv/DOPDu9aaDKk4AzjrJluxKCo0LrHReInXfL1i',
    email_verified = true
WHERE email = 'techsuru1@gmail.com';

UPDATE users 
SET email_verified = true
WHERE email = 'xer.xes.7.ai@gmail.com';


SELECT id, name, email FROM users WHERE id = 3;
