-- Enable uuid-ossp extension for gen_random_uuid() and uuid_ops operator class
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE coworking_spaces ( 
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    address TEXT NOT NULL,
    city VARCHAR(100),
    country VARCHAR(100),
    phone VARCHAR(50),
    email VARCHAR(255),
    website VARCHAR(255),
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    operating_hours JSONB NOT NULL DEFAULT '{
        "monday": {"open": "09:00", "close": "18:00"},
        "tuesday": {"open": "09:00", "close": "18:00"},
        "wednesday": {"open": "09:00", "close": "18:00"},
        "thursday": {"open": "09:00", "close": "18:00"},
        "friday": {"open": "09:00", "close": "18:00"},
        "saturday": {"open": null, "close": null},
        "sunday": {"open": null, "close": null}
    }'::jsonb,

    amenities JSONB DEFAULT '[]'::jsonb, -- ["wifi", "coffee", "parking", etc.]
    images JSONB DEFAULT '[]'::jsonb,
    image_link VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Rooms
CREATE TABLE rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coworking_space_id UUID NOT NULL REFERENCES coworking_spaces(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    room_number VARCHAR(50),
    floor VARCHAR(50),
    
    -- Capacity & physical attributes
    capacity INT NOT NULL CHECK (capacity > 0),
    square_meters DECIMAL(8,2),
    
    -- Description & amenities
    description TEXT,
    amenities JSONB DEFAULT '[]'::jsonb, -- ["projector", "whiteboard", "video_conf", etc.]
    images JSONB DEFAULT '[]'::jsonb,
    
    -- Room-specific settings
    hourly_rate DECIMAL(10,2), -- Optional, if rooms have different pricing
    image_link VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(coworking_space_id, name)
);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    
    avatar_url TEXT,
    phone VARCHAR(50),
    preferred_timezone VARCHAR(50) DEFAULT 'UTC',
    
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    
    -- Time range (using timerange for PostgreSQL 14+)
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_minutes INT GENERATED ALWAYS AS (
        EXTRACT(EPOCH FROM (end_time - start_time)) / 60
    ) STORED,

    status VARCHAR(50) NOT NULL DEFAULT 'confirmed',
    purpose TEXT,
    guest_count INT DEFAULT 1 CHECK (guest_count >= 1),

    CHECK (end_time > start_time),
    CHECK (EXTRACT(MINUTE FROM start_time) % 15 = 0), -- 15-min increments
    CHECK (EXTRACT(MINUTE FROM end_time) % 15 = 0),
    
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT exclude_overlapping_bookings EXCLUDE USING gist ( 
        room_id WITH =,
        tstzrange(start_time, end_time) WITH &&
    ) WHERE (status = 'confirmed' AND is_deleted = false)
);

CREATE INDEX idx_bookings_time_range ON bookings USING gist (room_id, tstzrange(start_time, end_time));
CREATE INDEX idx_bookings_user_id ON bookings(user_id);
CREATE INDEX idx_bookings_status ON bookings(status);

CREATE TABLE room_unavailability (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    is_recurring BOOLEAN DEFAULT false,
    recurring_pattern JSONB, -- For recurring unavailability
    
    CHECK (end_time > start_time),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_favorites (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    coworking_space_id UUID REFERENCES coworking_spaces(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, coworking_space_id)
);

CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    coworking_space_id UUID NOT NULL REFERENCES coworking_spaces(id) ON DELETE CASCADE,
    booking_id UUID REFERENCES bookings(id) ON DELETE SET NULL,
    
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, coworking_space_id, booking_id)
);

-- Audit log (for 12-factor compliance)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL, -- 'booking', 'room', 'space', etc.
    entity_id UUID,
    old_data JSONB,
    new_data JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_coworking_spaces_updated_at 
    BEFORE UPDATE ON coworking_spaces FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rooms_updated_at 
    BEFORE UPDATE ON rooms FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bookings_updated_at 
    BEFORE UPDATE ON bookings FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Seed Data
-- Note: Using fixed UUIDs for predictability in testing/development

-- Create a Coworking Space
INSERT INTO coworking_spaces (id, name, slug, address, city, country, is_active, image_link)
VALUES 
('11111111-1111-1111-1111-111111111111', 'Innovate Hub', 'innovate-hub-metropolis', '123 Tech Street', 'Metropolis', 'USA', true, 'https://images.unsplash.com/photo-1527192491265-7e15c55b1ed2?w=800&q=80'),
('11111111-2222-1111-1111-111111111111', 'Creator Space', 'creator-space-indy', '456 Art Ave', 'Indianapolis', 'USA', true, 'https://images.unsplash.com/photo-1497366216548-37526070297c?w=800&q=80'),
('11111111-1111-2222-1111-111111111111', 'The Foundry', 'the-foundry-la', '789 Maker Blvd', 'Los Angeles', 'USA', true, 'https://images.unsplash.com/photo-1582653291997-079a1c04e5d1?w=800&q=80'),
('11111111-1111-1111-2222-111111111111', 'Skolkovo Tech', 'skolkovo', '222 Tech Street', 'Moscow', 'Russia', true, 'https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=800&q=80');

-- Create a User
-- Password is 'password' (hashed with a placeholder, real app should use bcrypt)
INSERT INTO users (id, email, username, full_name, hashed_password, is_active)
VALUES ('22222222-2222-2222-2222-222222222222', 'test.user@example.com', 'testuser', 'Test User', '$2b$12$placeholderhashfortesting123', true);

-- Create a Room within the Coworking Space
INSERT INTO rooms (id, coworking_space_id, name, capacity, is_active, image_link)
VALUES 
('33333333-3333-3333-3333-333333333333', '11111111-1111-1111-1111-111111111111', 'The Think Tank', 10, true, 'https://images.unsplash.com/photo-1604328698692-f76ea9498e76?w=600&q=80'),
('44444444-4444-4444-4444-444444444444', '11111111-1111-1111-1111-111111111111', 'Focus Pod', 4, true, 'https://images.unsplash.com/photo-1517502884422-41eaead166d4?w=600&q=80'),
('55555555-5555-5555-5555-555555555555', '11111111-1111-1111-1111-111111111111', 'Boardroom', 20, true, 'https://images.unsplash.com/photo-1505409859467-3a796fd5798e?w=600&q=80'),
('66666666-6666-6666-6666-666666666666', '11111111-2222-1111-1111-111111111111', 'Creative Studio', 8, true, 'https://images.unsplash.com/photo-1556761175-5973dc0f32b7?w=600&q=80'),
('77777777-7777-7777-7777-777777777777', '11111111-2222-1111-1111-111111111111', 'The Idea Bubble', 6, true, 'https://images.unsplash.com/photo-1598257006458-087169a1f08d?w=600&q=80'),
('88888888-8888-8888-8888-888888888888', '11111111-2222-1111-1111-111111111111', 'Quiet Zone', 2, true, 'https://images.unsplash.com/photo-1497215848143-222dfd12a4c1?w=600&q=80'),
('99999999-9999-9999-9999-999999999999', '11111111-1111-2222-1111-111111111111', 'The Bubble', 10, true, 'https://images.unsplash.com/photo-1431540015161-0bf868a2d407?w=600&q=80'),
('33333333-3333-3333-3333-444444444444', '11111111-1111-2222-1111-111111111111', 'The Thought', 10, true, 'https://images.unsplash.com/photo-1503423571797-2d2bb372094a?w=600&q=80'),
('33333333-3333-3333-3333-555555555555', '11111111-1111-1111-2222-111111111111', 'The Great Thought', 10, true, 'https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=600&q=80'),
('33333333-3333-3333-3333-666666666666', '11111111-1111-1111-2222-111111111111', 'The Big Thought', 10, true, 'https://images.unsplash.com/photo-1517502884422-41eaead166d4?w=600&q=80');

-- You can use the following UUIDs in your API calls:
-- Coworking Space ID: 11111111-1111-1111-1111-111111111111
-- User ID: 22222222-2222-2222-2222-222222222222
-- Room ID: 33333333-3333-3333-3333-333333333333

-- Example Booking (optional, can be created via API)
-- INSERT INTO bookings (user_id, room_id, start_time, end_time, status)
-- VALUES ('22222222-2222-2222-2222-222222222222', '33333333-3333-3333-3333-333333333333', 
--         '2026-04-01T10:00:00Z', '2026-04-01T11:00:00Z', 'confirmed');