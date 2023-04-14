import React, { FC } from 'react'
import { createRoot } from 'react-dom/client'

import { App } from './App'

import './style/app.scss'

const Root: FC = () => {
    return <App />
}

createRoot(document.querySelector('#root')!).render(<Root />)
