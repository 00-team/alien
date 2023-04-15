import React, { FC } from 'react'

import { Routes, Route } from 'react-router-dom'

import { Dashboard } from 'pages/Dashboard'
import { Login } from 'pages/Login'

const App: FC = () => {
    return (
        <Routes>
            <Route path='login' element={<Login />} />
            <Route path='/' element={<Dashboard />} />
        </Routes>
    )
}

export { App }
