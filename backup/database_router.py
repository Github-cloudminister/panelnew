class MyDatabaseRouter:
    def db_for_read(self, model, **hints):
        """Directs read operations."""
        if model._meta.app_label == 'backup':
            return 'secondary'
        return 'default'

    def db_for_write(self, model, **hints):
        """Directs write operations."""
        if model._meta.app_label == 'backup':
            return 'secondary'
        return 'default'

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensures migrations are applied to both databases."""
        return True
