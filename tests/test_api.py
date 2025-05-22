import httpx
import pytest
from fastapi import status
from unittest.mock import AsyncMock, patch

from sqlalchemy import text
from app.schemas.user import User
from app.repositories.user_repository import UserRepository
from app.services.random_user_service import RandomUserService

@pytest.mark.asyncio
class TestUserAPI:
    async def test_get_user_success(self, db_session, test_client):
        repo = UserRepository(db_session)
        test_user = await repo.create_user({
            "gender": "male",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "location": "New York",
            "picture_url": "http://example.com/john.jpg"
        })
        
        response = test_client.get(f"/api/v1/{test_user.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_user.id
        assert data["first_name"] == "John"

    async def test_get_user_not_found(self, test_client):
        response = test_client.get("/api/v1/999999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "User not found"

    async def test_get_random_user(self, db_session, test_client):
        repo = UserRepository(db_session)
        await repo.create_user({
            "gender": "female",
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com",
            "phone": "987654321",
            "location": "London",
            "picture_url": "http://example.com/jane.jpg"
        })
        
        response = test_client.get("/api/v1/random")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data

@pytest.mark.asyncio
class TestFrontendRoutes:
    async def test_home_page(self, test_client):
        response = test_client.get("/")
        assert response.status_code == status.HTTP_200_OK
        assert "Random Users Manager" in response.text

    async def test_load_users_invalid_count(self, test_client):
        response = test_client.post("/load-users", data={"count": 0})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Count must be between 1 and 5000" in response.text

    async def test_user_detail_page(self, db_session, test_client):
        repo = UserRepository(db_session)
        user = await repo.create_user({
            "gender": "male",
            "first_name": "Detail",
            "last_name": "Test",
            "email": "detail@test.com",
            "phone": "1122334455",
            "location": "Test City",
            "picture_url": "http://test.com/detail.jpg"
        })
        response = test_client.get(f"/{user.id}")
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]
        content = response.text
        assert "Detail Test" in content  
        assert "user-photo-large" in content
        assert "http://test.com/detail.jpg" in content
        assert "detail@test.com" in content
        assert "1122334455" in content
        assert "Test City" in content
        assert 'class="back-link"' in content
        
@pytest.mark.asyncio
class TestUserRepository:
    async def test_create_user(self, db_session):
        repo = UserRepository(db_session)
        user = await repo.create_user({
            "gender": "female",
            "first_name": "Repo",
            "last_name": "Test",
            "email": "repo@test.com",
            "phone": "5566778899",
            "location": "Repo City",
            "picture_url": "http://test.com/repo.jpg"
        })
        
        assert user.id is not None
        assert user.first_name == "Repo"

    async def test_get_users_pagination(self, db_session):
        repo = UserRepository(db_session)
        for i in range(30):
            await repo.create_user({
                "gender": "male",
                "first_name": f"User{i}",
                "last_name": "Pagination",
                "email": f"user{i}@test.com",
                "phone": f"12345678{i:02d}",
                "location": "Pagination City",
                "picture_url": f"http://test.com/user{i}.jpg"
            })
        
        users_page1 = await repo.get_users(skip=0, limit=10)
        assert len(users_page1) == 10
        assert users_page1[0].first_name == "User0"
        
        users_page2 = await repo.get_users(skip=10, limit=10)
        assert len(users_page2) == 10
        assert users_page2[0].first_name == "User10"

@pytest.mark.asyncio
class TestAdditionalUserAPI:
    async def test_get_users_pagination_api(self, db_session, test_client):
        repo = UserRepository(db_session)
        for i in range(30):
            await repo.create_user({
                "gender": "male",
                "first_name": f"ApiUser{i}",
                "last_name": "Pagination",
                "email": f"apiuser{i}@test.com",
                "phone": f"87654321{i:02d}",
                "location": "ApiPagination City",
                "picture_url": f"http://test.com/apiuser{i}.jpg"
            })
        
        response = test_client.get("/?page=1")
        assert response.status_code == status.HTTP_200_OK
        assert "ApiUser0" in response.text
        assert "ApiUser21" not in response.text

        response = test_client.get("/?page=2")
        assert response.status_code == status.HTTP_200_OK
        assert "ApiUser0" not in response.text
        assert "ApiUser21" in response.text

    async def test_random_user_with_empty_db(self, test_client):
        """Тест получения случайного пользователя из пустой БД"""
        response = test_client.get("/api/v1/random")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "No users found"

@pytest.mark.asyncio
class TestAdditionalUserRepository:
    async def test_count_users(self, db_session):
        repo = UserRepository(db_session)
        initial_count = await repo.count_users()
        
        # Добавляем 5 пользователей
        for i in range(5):
            await repo.create_user({
                "gender": "female",
                "first_name": f"Count{i}",
                "last_name": "Test",
                "email": f"count{i}@test.com",
                "phone": f"11122233{i}",
                "location": "Count City",
                "picture_url": f"http://test.com/count{i}.jpg"
            })
        
        new_count = await repo.count_users()
        assert new_count == initial_count + 5

    async def test_get_random_user_from_empty_db(self, db_session):
        repo = UserRepository(db_session)
        await db_session.execute(text("DELETE FROM users"))
        await db_session.commit()
        
        user = await repo.get_random_user()
        assert user is None

@pytest.mark.asyncio
class TestAdditionalRandomUserService:
    async def test_fetch_users_network_error(self):
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = httpx.ConnectError("Network error")
            
            repo = UserRepository(AsyncMock())
            service = RandomUserService(repo)
            
            with pytest.raises(httpx.ConnectError):
                await service.fetch_users(10)

    @patch('app.services.random_user_service.RandomUserService.fetch_users')
    async def test_load_users_with_invalid_data(self, mock_fetch, db_session):
        mock_fetch.return_value = [{
            "gender": "male",
            "name": {"first": "Valid", "last": "User"},
            "email": "valid@test.com",
            "phone": "123456789",
            "location": {"street": {"number": 123, "name": "Main St"}},
            "picture": {"thumbnail": "http://test.com/valid.jpg"}
        }, {
            "invalid": "data" 
        }]
        
        repo = UserRepository(db_session)
        service = RandomUserService(repo)
        
        await service.load_users(2)
        
        users = await repo.get_users()
        assert len(users) == 1
        assert users[0].first_name == "Valid"

@pytest.mark.asyncio
class TestDatabaseInitialization:
    async def test_db_tables_created(self, db_engine):
        async with db_engine.connect() as conn:
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'"))
            table = result.fetchone()
            assert table is not None
            assert table[0] == "users"

    async def test_initial_data_loaded(self, db_session):
        repo = UserRepository(db_session)
        service = RandomUserService(repo)
        await service.load_users(1000)
        count = await repo.count_users()
        assert count > 0 

@pytest.mark.asyncio
class TestFrontendAdditional:
    async def test_load_users_success(self, test_client, db_session):
        await db_session.execute(text("DELETE FROM users"))
        await db_session.commit()
        
        response = test_client.post("/load-users", data={"count": 5}, follow_redirects=False)
        assert response.status_code == status.HTTP_303_SEE_OTHER 
        repo = UserRepository(db_session)
        count = await repo.count_users()
        assert count == 5

    async def test_user_detail_page_not_found(self, test_client):
        response = test_client.get("/999999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
class TestRandomUserServiceWithMocks:
    @patch('app.services.random_user_service.RandomUserService.fetch_users')
    async def test_load_users_success(self, mock_fetch, db_session):
        mock_fetch.return_value = [
            {
                "gender": "male",
                "name": {"first": "John", "last": "Doe"},
                "email": "john@example.com",
                "phone": "987-654-321",
                "location": {"street": {"number": 456, "name": "Oak Ave"}},
                "picture": {"thumbnail": "http://example.com/john.jpg"}
            }
        ]

        repo = UserRepository(db_session)
        service = RandomUserService(repo)
        await service.load_users(1)

        users = await repo.get_users()
        assert len(users) == 1
        assert users[0].first_name == "John"
        assert users[0].email == "john@example.com"

    @patch('app.services.random_user_service.RandomUserService.fetch_users')
    async def test_load_users_with_invalid_data(self, mock_fetch, db_session):
        mock_fetch.return_value = [
            {
                "invalid": "data"
            },
            {
                "gender": "female",
                "name": {"first": "Valid", "last": "User"},
                "email": "valid@example.com",
                "phone": "111-222-333",
                "location": {"street": {"number": 789, "name": "Pine St"}},
                "picture": {"thumbnail": "http://example.com/valid.jpg"}
            }
        ]

        repo = UserRepository(db_session)
        service = RandomUserService(repo)
        await service.load_users(2)

        users = await repo.get_users()
        assert len(users) == 1
        assert users[0].first_name == "Valid"

    @patch('app.services.random_user_service.RandomUserService.fetch_users')
    async def test_load_users_empty_response(self, mock_fetch, db_session):
        mock_fetch.return_value = []

        repo = UserRepository(db_session)
        service = RandomUserService(repo)
        await service.load_users(1)

        assert await repo.count_users() == 0

    @patch('app.services.random_user_service.RandomUserService.fetch_users')
    async def test_load_users(self, mock_fetch, db_session):
        mock_fetch.return_value = [{
            "gender": "male",
            "name": {"first": "Loaded", "last": "User"},
            "email": "loaded@test.com",
            "phone": "123456789",
            "location": {"street": {"number": 456, "name": "Oak Ave"}},
            "picture": {"thumbnail": "http://test.com/loaded.jpg"}
        }]
        
        repo = UserRepository(db_session)
        service = RandomUserService(repo)
        await service.load_users(1)
        
        users = await repo.get_users()
        assert len(users) == 1
        assert users[0].first_name == "Loaded"
