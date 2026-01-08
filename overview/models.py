from django.db import models


class Account(models.Model):
    pk = models.CompositePrimaryKey('account_login_number', 'time_last_update')
    trade_mode = models.IntegerField()
    balance = models.FloatField(blank=True, null=True)
    equity = models.FloatField(blank=True, null=True)
    profit = models.FloatField(blank=True, null=True)
    company = models.CharField(max_length=255, blank=True, null=True)
    currency = models.CharField(max_length=255, blank=True, null=True)
    time_last_update = models.DateTimeField()
    account_login_number = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'account'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class ClosedPositions(models.Model):
    position_id = models.BigIntegerField(primary_key=True)
    symbol = models.CharField(max_length=20)
    volume = models.FloatField()
    close_price = models.FloatField()
    swap = models.FloatField(blank=True, null=True)
    profit = models.FloatField(blank=True, null=True)
    fee = models.FloatField(blank=True, null=True)
    time_close = models.DateTimeField()
    time_open = models.DateTimeField(blank=True, null=True)
    open_price = models.FloatField(blank=True, null=True)
    weekday = models.CharField(max_length=255, blank=True, null=True)
    session = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'closed_positions'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class OpenPositions(models.Model):
    position_id = models.BigIntegerField(primary_key=True)
    symbol = models.CharField(max_length=20)
    volume = models.FloatField()
    price_open = models.FloatField()
    sl = models.FloatField(blank=True, null=True)
    tp = models.FloatField(blank=True, null=True)
    swap = models.FloatField(blank=True, null=True)
    profit = models.FloatField(blank=True, null=True)
    time_open = models.DateTimeField()
    time_last_update = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'open_positions'
