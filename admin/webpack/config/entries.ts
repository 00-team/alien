import { Entry } from 'webpack'

import { APP_DIR } from './path'

const Entries: Entry = {
    main: {
        import: APP_DIR,
    },
}

export default Entries
