import unittest
from app import app, db, User, List, Task
from werkzeug.security import generate_password_hash
import os

class TodoAppTestCase(unittest.TestCase):
    # Set up test environment before each test
    def setUp(self):
        """Set up test environment before each test"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        
        with app.app_context():
            db.create_all()
            
            # Create test users
            user1 = User(username='testuser1', password=generate_password_hash('password1'))
            user2 = User(username='testuser2', password=generate_password_hash('password2'))
            db.session.add_all([user1, user2])
            db.session.commit()

    # Clean up after each test
    def tearDown(self):
        """Clean up after each test"""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    # Helper function to log in
    def login(self, username, password):
        """Helper function to log in"""
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    # Helper function to log out
    def logout(self):
        """Helper function to log out"""
        return self.app.get('/logout', follow_redirects=True)

    # Helper function to create a list
    def create_list(self, name):
        """Helper function to create a list"""
        return self.app.post('/add_list', data=dict(
            name=name
        ), follow_redirects=True)

    # Helper function to create a task
    def create_task(self, content, list_id, parent_id=None):
        """Helper function to create a task"""
        data = dict(
            content=content,
            list_id=list_id
        )
        if parent_id:
            data['parent_id'] = parent_id
        return self.app.post('/add_task', data=data, follow_redirects=True)

    # Test that users can only see their own tasks
    def test_user_isolation(self):
        """Test that users can only see their own tasks"""
        # Login as user1
        self.login('testuser1', 'password1')
        
        # Create a list and task for user1
        self.create_list('User1 List')
        with app.app_context():
            list_id = List.query.filter_by(name='User1 List').first().id
        self.create_task('User1 Task', list_id)
        
        # Check if user1 sees their list and task
        response = self.app.get('/')
        self.assertIn(b'User1 List', response.data)
        self.assertIn(b'User1 Task', response.data)
        
        # Logout and login as user2
        self.logout()
        self.login('testuser2', 'password2')
        
        # Check that user2 doesn't see user1's content
        response = self.app.get('/')
        self.assertNotIn(b'User1 List', response.data)
        self.assertNotIn(b'User1 Task', response.data)

    # Test that users cannot modify other user's tasks
    def test_user_permissions(self):
        """Test that users cannot modify other user's tasks"""
        # Login as user1 and create a task
        self.login('testuser1', 'password1')
        self.create_list('User1 List')
        
        with app.app_context():
            list_id = List.query.filter_by(name='User1 List').first().id
            self.create_task('User1 Task', list_id)
            task_id = Task.query.filter_by(content='User1 Task').first().id
        
        # Logout and login as user2
        self.logout()
        self.login('testuser2', 'password2')
        
        # Try to complete user1's task
        self.app.get(f'/complete_task/{task_id}', follow_redirects=True)
        
        # Check if task still exists
        with app.app_context():
            task = Task.query.get(task_id)
            self.assertIsNotNone(task)

    # Test marking tasks as complete
    def test_task_completion(self):
        """Test marking tasks as complete"""
        self.login('testuser1', 'password1')
        self.create_list('Test List')
        
        with app.app_context():
            list_id = List.query.filter_by(name='Test List').first().id
            self.create_task('Test Task', list_id)
            task_id = Task.query.filter_by(content='Test Task').first().id
        
        # Mark task as complete
        self.app.get(f'/complete_task/{task_id}', follow_redirects=True)
        
        # Check if task is deleted (your implementation deletes completed tasks)
        with app.app_context():
            task = Task.query.get(task_id)
            self.assertIsNone(task)

    # Test collapsing and expanding a task
    def test_task_collapse(self):
        """Test collapsing and expanding a task"""
        self.login('testuser1', 'password1')
        self.create_list('Test List')
        
        with app.app_context():
            list_id = List.query.filter_by(name='Test List').first().id
            self.create_task('Parent Task', list_id)
            parent_id = Task.query.filter_by(content='Parent Task').first().id
            self.create_task('Child Task', list_id, parent_id)
        
        # Toggle collapse
        self.app.get(f'/toggle_collapse/{parent_id}', follow_redirects=True)
        
        # Check if task is collapsed
        with app.app_context():
            task = Task.query.get(parent_id)
            self.assertTrue(task.collapsed)

    # Test moving a top-level task to a different list
    def test_move_task(self):
        """Test moving a top-level task to a different list"""
        self.login('testuser1', 'password1')
        self.create_list('List A')
        self.create_list('List B')
        
        with app.app_context():
            list_a_id = List.query.filter_by(name='List A').first().id
            list_b_id = List.query.filter_by(name='List B').first().id
            self.create_task('Task to Move', list_a_id)
            task_id = Task.query.filter_by(content='Task to Move').first().id
        
        # Move task to List B
        self.app.post('/move_task', data=dict(
            task_id=task_id,
            new_list_id=list_b_id
        ), follow_redirects=True)
        
        # Check if task moved to List B
        with app.app_context():
            task = Task.query.get(task_id)
            self.assertEqual(task.list_id, list_b_id)

# Run the tests if the script is executed
if __name__ == '__main__':
    unittest.main()