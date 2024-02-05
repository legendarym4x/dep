import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.user import UserModel

from src.entity.models import User
from src.repository.users import get_user_by_email, create_user, update_token, confirmed_email, update_avatar_url, \
    set_new_password, update_reset_token


class TestUser(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session = AsyncMock(spec=AsyncSession)
        self.user = User()

    async def test_get_user_by_email(self):
        mocked_user = MagicMock()
        mocked_user.scalar_one_or_none.return_value = self.user
        self.session.execute.return_value = mocked_user
        result = await get_user_by_email(email='test@email.com', db=self.session)
        self.assertEqual(result, self.user)

    @patch('src.repository.users.Gravatar')
    @patch('src.repository.users.User')
    async def test_create_user_success(self, MockUser, MockGravatar):
        mock_db_session = self.session
        mock_gravatar_instance = MockGravatar.return_value
        mock_gravatar_instance.get_image.return_value = 'http://example.com/avatar.jpg'

        user_data = UserModel(email='test@email.com', username='Test User', password='Password')
        real_user_instance = User(**user_data.model_dump(), avatar='http://example.com/avatar.jpg')
        mock_user_instance = MockUser.return_value = real_user_instance
        mock_user_instance.email = user_data.email
        mock_user_instance.username = user_data.username
        mock_user_instance.avatar = 'http://example.com/avatar.jpg'

        created_user = await create_user(user_data, mock_db_session)
        mock_db_session.add.assert_called_once_with(mock_user_instance)
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(mock_user_instance)

        self.assertEqual(created_user.email, user_data.email)
        self.assertEqual(created_user.username, user_data.username)
        self.assertEqual(created_user.avatar, 'http://example.com/avatar.jpg')

    @patch('src.repository.users.Gravatar')
    @patch('src.repository.users.User')
    async def test_create_user_with_gravatar_error(self, MockUser, MockGravatar):
        mock_db_session = self.session
        mock_gravatar_instance = MockGravatar.return_value
        mock_gravatar_instance.get_image.side_effect = Exception('Gravatar error')

        user_data = UserModel(email='test@email.com', username='Test User', password='Password')
        mock_user_instance = MockUser.return_value = User(**user_data.model_dump(), avatar=None)
        mock_user_instance.email = 'test@email.com'
        mock_user_instance.username = 'Test User'

        created_user = await create_user(user_data, mock_db_session)
        mock_db_session.add.assert_called_once_with(mock_user_instance)
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(created_user)

        self.assertEqual(created_user.email, user_data.email)
        self.assertEqual(created_user.username, user_data.username)
        self.assertIsNone(created_user.avatar)

    @patch('src.repository.users.User')
    async def test_update_token(self, Mock_User):
        mock_user = Mock_User.return_value
        token = 'new token'
        await update_token(mock_user, token, self.session)
        self.assertEqual(token, mock_user.refresh_token)
        self.session.commit.assert_called_once()

    @patch('src.repository.users.get_user_by_email')
    async def test_confirmed_email(self, MockGetUserByEmail):
        mock_get = MockGetUserByEmail.return_value = User()
        await confirmed_email('test@email.com', self.session)
        self.assertEqual(mock_get.confirmed, True)
        self.session.commit.assert_called_once()

    @patch('src.repository.users.get_user_by_email')
    async def test_update_avatar(self, MockGetUserByEmail):
        mock_get = MockGetUserByEmail.return_value = User()
        result = await update_avatar_url('test@email.com', 'http://example.com', self.session)
        self.assertEqual(mock_get.avatar, 'http://example.com')
        self.assertEqual(result.avatar, 'http://example.com')
        self.session.commit.assert_called_once()
        self.assertEqual(result, mock_get)

    @patch('src.repository.users.get_user_by_email')
    async def test_set_new_password(self, mocked_get_user_by_email):
        email = "test@email.com"
        new_password = "new_password"

        mocked_user = MagicMock()
        mocked_user.password = "old_password"
        mocked_get_user_by_email.return_value = mocked_user
        mocked_db = MagicMock(AsyncSession)

        result = await set_new_password(email, new_password, mocked_db)

        self.assertEqual(result, mocked_user)
        self.assertEqual(mocked_user.password, new_password)
        mocked_db.commit.assert_called_once()

    @patch('src.repository.users.get_user_by_email')
    async def test_update_reset_token(self, mocked_get_user_by_email):
        # Given
        user = User()
        reset_token = "new_reset_token"

        mocked_db = MagicMock(AsyncSession)

        real_db = MagicMock(AsyncSession)
        real_db.commit.return_value = None

        result = await update_reset_token(user, reset_token, real_db)

        self.assertEqual(result, user)
        self.assertEqual(user.password_reset_token, reset_token)
        real_db.commit.assert_called_once()


if __name__ == '__main__':
    unittest.main()
