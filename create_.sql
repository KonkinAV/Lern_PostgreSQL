-- Таблица для исполнителей
CREATE TABLE IF NOT EXISTS artists (
    artist_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- Таблица для жанров
CREATE TABLE IF NOT EXISTS genres (
    genre_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- Таблица для связи исполнителей и жанров (многие-ко-многим)
CREATE TABLE IF NOT EXISTS artist_genre (
    artist_id INTEGER REFERENCES artists(artist_id) ON DELETE CASCADE,
    genre_id INTEGER REFERENCES genres(genre_id) ON DELETE CASCADE,
    CONSTRAINT pk_artist_genre PRIMARY KEY (artist_id, genre_id)
);

-- Таблица для альбомов
CREATE TABLE IF NOT EXISTS albums (
    album_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    release_year INTEGER NOT NULL
);

-- Таблица для связи исполнителей и альбомов (многие-ко-многим)
CREATE TABLE IF NOT EXISTS artist_album (
    artist_id INTEGER REFERENCES artists(artist_id) ON DELETE CASCADE,
    album_id INTEGER REFERENCES albums(album_id) ON DELETE CASCADE,
    CONSTRAINT pk_artist_album PRIMARY KEY (artist_id, album_id)
);

-- Таблица для треков
CREATE TABLE IF NOT EXISTS tracks (
    track_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    duration_seconds INTEGER,
    album_id INTEGER REFERENCES albums(album_id) ON DELETE CASCADE NOT NULL
);

-- Таблица для сборников
CREATE TABLE IF NOT EXISTS compilations (
    compilation_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    release_year INTEGER NOT NULL
);

-- Таблица для связи сборников и треков (многие-ко-многим)
CREATE TABLE IF NOT EXISTS compilation_track (
    compilation_id INTEGER REFERENCES compilations(compilation_id) ON DELETE CASCADE,
    track_id INTEGER REFERENCES tracks(track_id) ON DELETE CASCADE,
    CONSTRAINT pk_compilation_track PRIMARY KEY (compilation_id, track_id)
);
