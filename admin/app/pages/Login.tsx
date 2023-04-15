import React, { FC } from 'react'

import './style/login.scss'

const Login: FC = () => {
    return (
        <div className='login-container'>
            <div className='form'>
                <h1>Login</h1>
                <input type='text' placeholder='Username' />
                <input type='password' placeholder='Password' />
                <button className='btn'>Login</button>
            </div>
        </div>
    )
}

export { Login }
