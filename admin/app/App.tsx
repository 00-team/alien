import React, { FC } from 'react'

const App: FC = () => {
    return (
        <div className='container'>
            <div className='sidebar'>
                <ul>
                    <li>Dashboard</li>
                    <li>Users</li>
                    <li>Settings</li>
                </ul>
            </div>
            <div className='main'>
                <h1>Welcome to the Dark Admin Panel</h1>
            </div>
        </div>
    )
}

export { App }
