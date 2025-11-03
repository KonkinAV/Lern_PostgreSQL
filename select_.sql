-- Задание №2
-- Название и продолжительность самого длительного трека
SELECT title,  duration_seconds FROM tracks
ORDER BY duration_seconds DESC
LIMIT 1;

-- Название треков, продолжительность которых не мнее 3,5 минут (210 секунд)
SELECT title FROM tracks
WHERE duration_seconds >= 210;

-- Название сборников, вышедших в период с 2018 по 2020 год включительно
SELECT title FROM compilations
WHERE release_year BETWEEN 2018 AND 2020;

-- Исполнители, чье имя состоит из одного слова
SELECT name FROM artists
WHERE TRIM(name) NOT LIKE '% %';

-- Название треков, которые содержат слово мой или my
SELECT title FROM tracks
WHERE title ILIKE 'Мой%' OR title ILIKE '%my%';

-- Задание №3
-- Количество исполнителей в каждом жанре
SELECT
    g.name AS genre_name,
    COUNT(ag.artist_id) AS artist_count
FROM
    genres g
LEFT JOIN
    artist_genre ag ON g.genre_id = ag.genre_id
GROUP BY
    g.genre_id, g.name
ORDER BY
    artist_count DESC, genre_name ASC;

-- Количество треков, вошедших в альбомы 2019 - 2020 годов
SELECT
    COUNT(t.track_id) AS total_tracks_2019_2020
FROM
    tracks t
JOIN
    albums a ON t.album_id = a.album_id
WHERE
    a.release_year BETWEEN 2019 AND 2020;

-- Средняя продолжительность треков по каждому альболму
SELECT
    a.title AS album_title,
    AVG(t.duration_seconds) AS average_duration
FROM
    albums a
JOIN
    tracks t ON a.album_id = t.album_id
GROUP BY
    a.album_id, a.title
ORDER BY
    a.title;

-- Все исполнители, которые не выпустили альболмы в 2020 году
SELECT
    a.name
FROM
    artists a
LEFT JOIN
    albums al ON a.artist_id = al.album_id AND al.release_year = 2020
WHERE
    al.album_id IS NULL;

-- Названия сборников, в которых присутствует конкретный исполнитель (Баста)
SELECT DISTINCT
    c.title AS compilation_title
FROM
    compilations c
JOIN
    compilation_track ct ON c.compilation_id = ct.compilation_id
JOIN
    tracks t ON ct.track_id = t.track_id
JOIN
    artist_album aa ON t.album_id = aa.album_id
JOIN
    artists a ON aa.artist_id = a.artist_id
WHERE
    a.name ILIKE 'Баста';

-- Задание №4
-- Названия альбомов, в которых присудствуют исполнители более чем одного жанра
WITH ArtistGenreCounts AS (
    -- 1. Считаем количество жанров у каждого исполнителя
    SELECT
        artist_id,
        COUNT(genre_id) AS genre_count
    FROM
        artist_genre
    GROUP BY
        artist_id
    HAVING
        COUNT(genre_id) > 1 -- Отбираем только тех, у кого больше 1 жанра
),
MultiGenreArtists AS (
    -- 2. Получаем список ID исполнителей, подходящих под условие выше
    SELECT
        artist_id
    FROM
        ArtistGenreCounts
)
-- 3. Выводим названия альбомов этих исполнителей
SELECT DISTINCT
    a.title AS album_title
FROM
    albums a
JOIN
    artist_album aa ON a.album_id = aa.album_id
JOIN
    MultiGenreArtists mga ON aa.artist_id = mga.artist_id;

-- Наименования треков, которые не входят в сборники
SELECT title AS track_title FROM tracks
WHERE track_id NOT IN (SELECT DISTINCT track_id FROM compilation_track);
-- У меня вывод пустой (так как все треки входят в какой то сборник)

-- Исполнитель или исполнители, написавшие самый короткий по продолжительности трек
SELECT DISTINCT
    a.name AS artist_name,
    t.title AS track_title,
    t.duration_seconds
FROM
    artists a
JOIN
    artist_album aa ON a.artist_id = aa.artist_id
JOIN
    albums al ON aa.album_id = al.album_id
JOIN
    tracks t ON al.album_id = t.album_id
WHERE
    t.duration_seconds = (SELECT MIN(duration_seconds) FROM tracks WHERE duration_seconds IS NOT NULL)
ORDER BY
    a.name;

-- Названия альбомов, содержащих наименьшее количество треков
SELECT
    a.title AS album_title,
    COUNT(t.track_id) AS track_count
FROM
    albums a
JOIN
    tracks t ON a.album_id = t.album_id
GROUP BY
    a.album_id, a.title
HAVING
    COUNT(t.track_id) = (
        -- Подзапрос: находим минимальное количество треков среди всех альбомов
        SELECT MIN(tracks_in_album)
        FROM (
            SELECT
                COUNT(track_id) AS tracks_in_album
            FROM
                tracks
            GROUP BY
                album_id
        ) AS Counts
    )
ORDER BY
    a.title;
-- У меня все альболмы содержат по одному треку

