import React, { FC } from 'react'
import { createRoot } from 'react-dom/client'

import { BrowserRouter } from 'react-router-dom'

import { App } from './App'

import './style/app.scss'

const Root: FC = () => {
    return (
        <BrowserRouter>
            <App />
        </BrowserRouter>
    )
}

createRoot(document.querySelector('#root')!).render(<Root />)
