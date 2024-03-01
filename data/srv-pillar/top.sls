base:
  'os:Ubuntu':
    - match: grain
    - ubuntu.users
  'os:RedHat':
    - match: grain
    - rhel.users
