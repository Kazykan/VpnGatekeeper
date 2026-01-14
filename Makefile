reset-db:
	docker exec -it vpngatekeeper-db-1 psql -U user -d django_db -c "DROP SCHEMA public CASCADE;"
	docker exec -it vpngatekeeper-db-1 psql -U user -d django_db -c "CREATE SCHEMA public;"
	docker exec -it django_api python manage.py makemigrations myapp
	docker exec -it django_api python manage.py migrate