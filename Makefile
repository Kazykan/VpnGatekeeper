reset-db:
	docker exec -it postgres_db psql -U user -d django_db -c "DROP SCHEMA public CASCADE;"
	docker exec -it postgres_db psql -U user -d django_db -c "CREATE SCHEMA public;"
	docker exec -it django_api python manage.py makemigrations myapp
	docker exec -it django_api python manage.py migrate