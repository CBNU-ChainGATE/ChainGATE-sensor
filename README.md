# Sensor API server

Sensor API server

# How to start the Sensor API server

```
$ cd ChainGATE-sensor/
$ python3 app.py
```

# Sensor API GUIDE

### 1. /finger/enroll [POST]

{ 'employee_id': 사번 }

|      Key      | Value |   Type   |
| :-----------: | :---: | :------: |
| "employee_id" | 사번  | char(10) |

### 2. /finger/delete [POST]

{ 'employee_id': 사번 }

|      Key      | Value |   Type   |
| :-----------: | :---: | :------: |
| "employee_id" | 사번  | char(10) |

### 3. /finger/search [GET]

**-> response**: { 'employee_id': 사번 }

### 4. /door [POST]

{ 'value': value }

|   Key   |  Value   | Type |
| :-----: | :------: | :--: |
| "value" | 0 또는 1 | int  |
