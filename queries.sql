-- Highway points, Demo Spatial in Values tab
SELECT osm_id, highway, tags, way
     FROM public.planet_osm_point pop 
     WHERE highway IS NOT null;
     

    
    
    
-- Traffic_signals
SELECT osm_id, highway, tags, way
     FROM public.planet_osm_point pop 
     WHERE highway like 'traffic_signals'; 
    
       

-- Highway lines, Demo Spatial tab.
-- Selection is random 200 rows...
SELECT osm_id, highway, way
   FROM public.planet_osm_line
   WHERE highway IS NOT null;
   

  
  
-- Get polygon city
select name,admin_level,  way 
	from planet_osm_polygon 
	where name ilike '%casablanca%' and admin_level = '5' ;
	



-- Add spatial join (ST Contains) to filter for specific area
SELECT l.osm_id, l.highway, p.way, l.way
     FROM public.planet_osm_line l
     INNER JOIN public.planet_osm_polygon p
           ON ST_Contains (p.way, l.way) AND p.name ilike '%casablanca%' and p.admin_level = '5'
     WHERE l.highway IS NOT null;
    
    
    
    
-- Add spatial join (ST Contains) to filter for specific area
SELECT l.osm_id, l.highway, l.tags, p.way, l.way
     FROM public.planet_osm_line l
     INNER JOIN public.planet_osm_polygon p
           ON ST_Contains (p.way, l.way) AND p.name ilike '%casablanca%' and p.admin_level = '5'
     WHERE l.highway = 'primary';
        
   

-- Quality Control on tags, using skeys()/ svals()
SELECT skeys (tags) AS tag_key, svals(tags) AS tag_value, COUNT (*) AS cnt
    FROM public.planet_osm_line
    WHERE highway = 'primary'
    GROUP BY tag_key, tag_value
    ORDER BY tag_key DESC      
      
      
      
    
--Spatial calculation: ST Length() -- 2D Cartesian length
SELECT p.name, l.highway, p.way, SUM(ST_Length(l.way)) / 1000 AS way_length
       FROM public.planet_osm_line l
       INNER JOIN public.planet_osm_polygon p
             ON ST_Contains (p.way, l.way) AND p.name ilike '%casablanca%' AND p.admin_level = '5'
	   WHERE l.highway IS NOT NULL
	   GROUP BY p.name, l.highway, p.way
	   ORDER BY way_length DESC
    
	   
	   
	   
	   
	   
    