import { CSSProperties, forwardRef } from 'react';
import { FormattedMessage } from 'react-intl';
import { Button, Icon, IconSize } from '@blueprintjs/core';
import { Tooltip2 as Tooltip } from '@blueprintjs/popover2';
import c from 'classnames';
import { Entity } from '@alephdata/followthemoney';
import { useTimelineItemKeyboardNavigation } from '../util';
import TimelineItemCaption from '../TimelineItemCaption';

import './TimelineListItem.scss';

type TimelineListItemProps = {
  entity: Entity;
  color: string;
  writeable?: boolean;
  selected?: boolean;
  muted?: boolean;
  showEndDate?: boolean;
  onSelect: (entity: Entity) => void;
  onRemove: (entity: Entity) => void;
};

const TimelineListItem = forwardRef<HTMLTableRowElement, TimelineListItemProps>(
  (props, ref) => {
    const {
      entity,
      color,
      writeable,
      selected,
      muted,
      showEndDate = false,
      onSelect,
      onRemove,
    } = props;

    const style: CSSProperties = {
      ['--timeline-item-color' as string]: color,
    };

    const keyboardProps = useTimelineItemKeyboardNavigation(entity, onSelect);

    const start = entity.getTemporalStart();
    const end = entity.getTemporalEnd();

    return (
      <tr
        {...keyboardProps}
        ref={ref}
        tabIndex={0}
        onClick={() => onSelect(entity)}
        style={style}
        className={c(
          'TimelineListItem',
          muted && 'TimelineListItem--muted',
          selected && 'TimelineListItem--selected'
        )}
      >
        <td className="TimelineListItem__date">
          {start?.value}
          <br />
          <span className="TimelineListItem__property">
            {start?.property.label}
          </span>
        </td>
        {showEndDate && (
          <td className="TimelineListItem__date">
            {end?.value}
            <br />
            <span className="TimelineListItem__property">
              {end?.property.label}
            </span>
          </td>
        )}
        <td className="TimelineListItem__caption">
          <strong>
            <TimelineItemCaption entity={entity} />
          </strong>
        </td>
        {writeable && (
          <td className="TimelineListItem__actions">
            <Tooltip
              placement="top"
              content={
                <FormattedMessage
                  id="timeline.item.remove.long"
                  defaultMessage="Remove from timeline"
                />
              }
            >
              <Button minimal small onClick={() => onRemove(entity)}>
                <Icon icon="trash" size={IconSize.STANDARD} />
                <span className="visually-hidden">
                  <FormattedMessage
                    id="timeline.item.remove.short"
                    defaultMessage="Remove"
                  />
                </span>
              </Button>
            </Tooltip>
          </td>
        )}
      </tr>
    );
  }
);

export default TimelineListItem;
