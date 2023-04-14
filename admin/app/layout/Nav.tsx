import React, { FC } from 'react'

import { Text, Button } from '@mantine/core'
import { Link } from 'react-router-dom'

const Nav: FC = () => {
    return (
        <div style={{ minWidth: '200px', padding: '16px' }}>
            <Text weight={700} size='lg' style={{ marginBottom: '16px' }}>
                Admin Panel
            </Text>
            <Button
                variant='outline'
                color='blue'
                fullWidth
                style={{ marginBottom: '16px' }}
                component={Link}
                to='/posts'
            >
                Posts
            </Button>
            <Button
                variant='outline'
                color='blue'
                fullWidth
                style={{ marginBottom: '16px' }}
                component={Link}
                to='/users'
            >
                Users
            </Button>
        </div>
    )
}

export default Nav
