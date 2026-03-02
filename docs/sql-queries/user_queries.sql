select * from public.user

select u.id as "User Id", u.email, u.full_name as "Name" from public.user u

select u.id as "User Id", u.email, u.full_name as "Name", i.name as "Institute Name" from public.user u left join public.institution i on u.institution_id = i.id where u.institution_id = 1   

