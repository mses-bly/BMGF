from django.utils import timezone
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.mail import send_mail
from django.db import models

# Create your models here.
from django.utils.http import urlquote


class MoneyUserManager(BaseUserManager):
    def _create_user(self, email, password,
                     is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        now = timezone.now()
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email,
                          is_staff=is_staff, is_active=True,
                          is_superuser=is_superuser, last_login=now,
                          date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, False, False,
                                 **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, True,
                                 **extra_fields)


class MoneyUser(AbstractBaseUser, PermissionsMixin):
    """
    A fully featured User model with admin-compliant permissions that uses
    a full-length email field as the username.

    Email and password are required. Other fields are optional.
    """
    email = models.EmailField(_('email address'), max_length=254, unique=True)
    first_name = models.CharField(_('first name'), max_length=30)
    last_name = models.CharField(_('last name'), max_length=30)
    is_staff = models.BooleanField(_('staff status'), default=False,
                                   help_text=_('Designates whether the user can log into this admin site.'))
    is_active = models.BooleanField(_('active'), default=True,
                                    help_text=_('Designates whether this user should be treated as '
                                                'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    MALE = 'M'
    FEMALE = 'F'
    GENDERS = (
        (MALE, "Male"),
        (FEMALE, "Female"),
    )

    gender = models.CharField(max_length=1, choices=GENDERS)

    birth_day = models.DateField()

    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$',
                                 message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(validators=[phone_regex], max_length=15)  # validators should be a list

    objects = MoneyUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'gender', 'birth_day']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_absolute_url(self):
        return "/users/%s/" % urlquote(self.email)

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Returns the short name for the user."""
        return self.first_name

    def email_user(self, subject, message, from_email=None):
        send_mail(subject, message, from_email, [self.email])


# class Pool(models.Model):
#     name = models.CharField(_('Money Pool Name'), max_length=30)
#     minimum_deposit = models.FloatField(_("Minimum Deposit"))
#     creation_date = models.DateTimeField(blank=True, default=timezone.now)
#
#
# class PoolMembership(models.Model):
#     user = models.ForeignKey(MoneyUser, related_name='pools')
#     group = models.ForeignKey(Pool, related_name='users')
#     date_joined = models.DateTimeField(blank=True, default=timezone.now)


class UserContribution(models.Model):
    user = models.ForeignKey(MoneyUser, related_name='contributions')
    # group = models.ForeignKey(Pool, related_name='contributions')
    txn_amount = models.FloatField()
    balance = models.FloatField(blank=True)
    time = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        contribs = UserContribution.objects.filter(user=self.user).order_by('-time')
        if contribs:
            bal = contribs[0].balance
            print("He has contributions")
            print("Last contribution balance: " + str(bal))
            self.balance = bal + self.txn_amount
        else:
            self.balance = self.txn_amount
        super(UserContribution, self).save(*args, **kwargs)


class UserPointMovement(models.Model):
    user = models.ForeignKey(MoneyUser, related_name='pointsmovements')
    # group = models.ForeignKey(Pool, related_name='pointsmovements')
    txn_amount = models.IntegerField()
    balance = models.IntegerField(blank=True)
    time = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        contribs = UserPointMovement.objects.filter(user=self.user).order_by('-time')
        if contribs:
            # We take the first
            bal = contribs[0].balance
            print("He has contributions")
            print("Last contribution balance: " + str(bal))
            self.balance = bal + self.txn_amount
        else:
            self.balance = self.txn_amount
        super(UserPointMovement, self).save(*args, **kwargs)


class Lottery(models.Model):
    name = models.CharField(_('Lottery Name'), max_length=30)
    description = models.CharField(_('Lottery description'), max_length=200)
    total_tickets = models.IntegerField()


class UserLotteryTicketMovement(models.Model):
    user = models.ForeignKey(MoneyUser)
    lottery = models.ForeignKey(Lottery)
    txn_amount = models.IntegerField()
    balance = models.IntegerField(blank=True)
    time = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        contribs = UserLotteryTicketMovement.objects.filter(user=self.user, group=self.group).order_by('-time')
        if contribs:
            # We take the first
            bal = contribs[0].balance
            print("He has tickets")
            print("Last lottery ticket balance: " + str(bal))
            self.balance = bal + self.txn_amount
        else:
            self.balance = self.txn_amount
        super(UserLotteryTicketMovement, self).save(*args, **kwargs)


# Lotery Users

class UserGoal(models.Model):
    user = models.ForeignKey(MoneyUser, related_name='goals')
    name = models.CharField(_('Goal Name'), max_length=30)
    description = models.CharField(_('Goal description'), max_length=200)
    amount = models.FloatField()
